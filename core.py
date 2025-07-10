#!/usr/bin/env python3
#
# Copyright 2025 Dimitry Polivaev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Core functionality for YouTube Subtitles to Chapter Timecodes
"""

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable
import yt_dlp
import google.generativeai as genai

# ========================================
# CONFIGURATION
# ========================================

# Model settings
DEFAULT_MODEL = 'gemini-2.5-pro'
AVAILABLE_MODELS = [
    'gemini-2.5-pro', 
    'gemini-2.5-flash'
]

# Gemini prompt for generating chapter timecodes
GEMINI_PROMPT = """Break down this video content into chapters 
and generate timecodes in mm:ss format (e.g., 00:10, 05:30, 59:59, 1:01:03). 
Each chapter should be formatted as: timecode - chapter title. 
Generate the chapter titles in the same language as the subtitles."""

# Major languages for auto-selection priority
MAJOR_LANGUAGES = [
    'en', 'es', 'fr', 'de', 'it', 'pt', 
    'ru', 'uk', 'ja', 'ko', 'zh', 'ar'
]

class SubtitleInfo:
    """Container for subtitle information."""
    def __init__(self, language: str, file_path: str, content: str):
        self.language = language
        self.file_path = file_path
        self.content = content

class ProcessingOptions:
    """Container for processing options."""
    def __init__(self, 
                 language: Optional[str] = None,
                 api_key: Optional[str] = None,
                 model: str = DEFAULT_MODEL,
                 keep_files: bool = False,
                 output_dir: Optional[str] = None,
                 show_subtitles: bool = False,
                 quiet: bool = False):
        self.language = language
        self.api_key = api_key
        self.model = model
        self.keep_files = keep_files
        self.output_dir = output_dir
        self.show_subtitles = show_subtitles
        self.quiet = quiet

class YouTubeProcessor:
    """Main class for processing YouTube videos."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the processor.
        
        Args:
            progress_callback: Optional callback function to report progress
        """
        self.progress_callback = progress_callback
        self.temp_files = []
    
    def _report_progress(self, message: str):
        """Report progress to callback or print."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def get_available_languages(self, youtube_url: str) -> Dict[str, List[str]]:
        """
        Get available subtitle languages for a YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dictionary with language categories and their codes
        """
        try:
            clean_url = self._clean_url(youtube_url)
            info_opts = {'quiet': True}
            
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                available_subs = info.get('automatic_captions', {})
                
                if not available_subs:
                    return {}
                
                # Group languages by type
                orig_langs = []
                regular_langs = []
                auto_langs = []
                
                covered_langs = set()
                
                for lang in available_subs.keys():
                    if lang.endswith('-orig'):
                        base_lang = lang[:-5]
                        orig_langs.append(base_lang)
                        covered_langs.add(base_lang)
                    elif '-' not in lang:
                        regular_langs.append(lang)
                        covered_langs.add(lang)
                
                for lang in available_subs.keys():
                    if '-' in lang and not lang.endswith('-orig'):
                        base_lang = lang.split('-')[0]
                        if base_lang not in covered_langs:
                            auto_langs.append(base_lang)
                            covered_langs.add(base_lang)
                
                return {
                    'original': sorted(set(orig_langs)),
                    'standard': sorted(set(regular_langs)),
                    'auto_translated': sorted(set(auto_langs))
                }
                
        except Exception as e:
            self._report_progress(f"Error checking available languages: {e}")
            return {}
    
    def _clean_url(self, url: str) -> str:
        """Clean URL from shell escaping."""
        return url.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&')
    
    def _select_language(self, available_subs: Dict, language: Optional[str]) -> str:
        """Select the best language based on availability and preferences."""
        if language:
            # User specified a language
            if f"{language}-orig" in available_subs:
                return f"{language}-orig"
            elif language in available_subs:
                return language
            else:
                # Look for auto-translated versions
                auto_candidates = []
                for lang_code in available_subs.keys():
                    if '-' in lang_code and not lang_code.endswith('-orig'):
                        parts = lang_code.split('-')
                        if len(parts) == 2 and (parts[0] == language or parts[1] == language):
                            auto_candidates.append(lang_code)
                
                if auto_candidates:
                    source_translations = [lang for lang in auto_candidates if lang.endswith(f'-{language}')]
                    return source_translations[0] if source_translations else auto_candidates[0]
                
                raise ValueError(f"Requested language '{language}' not found")
        else:
            # Auto-select language
            available_langs = list(available_subs.keys())
            
            # First, try original languages
            orig_langs = [lang for lang in available_langs if lang.endswith('-orig')]
            if orig_langs:
                return orig_langs[0]
            
            # Then try major languages
            for major in MAJOR_LANGUAGES:
                if major in available_langs:
                    return major
            
            # Finally, use first available
            return available_langs[0]
    
    def download_subtitles(self, youtube_url: str, language: Optional[str] = None, 
                         output_dir: Optional[str] = None) -> SubtitleInfo:
        """
        Download auto-generated subtitles from YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            language: Optional language code for subtitles
            output_dir: Directory to save subtitles
            
        Returns:
            SubtitleInfo object with language, file path, and content
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        clean_url = self._clean_url(youtube_url)
        self._report_progress(f"Processing URL: {clean_url}")
        
        # Check available subtitles
        info_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            try:
                info = ydl.extract_info(clean_url, download=False)
                available_subs = info.get('automatic_captions', {})
                
                if not available_subs:
                    raise ValueError("No auto-generated subtitles found")
                
                # Select language
                selected_lang = self._select_language(available_subs, language)
                self._report_progress(f"Selected language: {selected_lang}")
                
            except Exception as e:
                raise ValueError(f"Error checking subtitles: {e}")
        
        # Download subtitles
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [selected_lang],
            'subtitlesformat': 'srt',
            'skip_download': True,
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([clean_url])
                
                # Find downloaded subtitle file
                subtitle_files = list(Path(output_dir).glob('*.srt'))
                if not subtitle_files:
                    raise FileNotFoundError("No subtitle files were downloaded")
                
                subtitle_file = str(subtitle_files[0])
                self.temp_files.append(subtitle_file)
                
                # Read content
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self._report_progress("Subtitles downloaded successfully")
                
                return SubtitleInfo(
                    language=selected_lang,
                    file_path=subtitle_file,
                    content=content
                )
                
            except Exception as e:
                raise ValueError(f"Error downloading subtitles: {e}")
    
    def process_with_gemini(self, subtitle_content: str, api_key: str, 
                          model_name: str = DEFAULT_MODEL) -> str:
        """
        Process subtitle content with Gemini AI.
        
        Args:
            subtitle_content: Content of the subtitle file
            api_key: Gemini API key
            model_name: Name of the Gemini model to use
            
        Returns:
            AI-generated chapter timecodes with titles
        """
        try:
            self._report_progress(f"Processing with {model_name}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Use specified model
            model = genai.GenerativeModel(model_name)
            
            # Combine prompt with content
            full_prompt = f"{GEMINI_PROMPT}\n\nSubtitles:\n{subtitle_content}"
            
            # Generate response
            response = model.generate_content(full_prompt)
            
            self._report_progress("Processing completed successfully")
            
            return response.text
            
        except Exception as e:
            raise ValueError(f"Error processing with Gemini: {e}")
    
    def save_content(self, content: str, filename: str) -> str:
        """
        Save content to a file.
        
        Args:
            content: Content to save
            filename: Base filename
            
        Returns:
            Path to saved file
        """
        try:
            # Create safe filename
            safe_filename = re.sub(r'[^\w\s-]', '', filename).strip()
            safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
            
            filepath = f"{safe_filename}.txt"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filepath
            
        except Exception as e:
            raise ValueError(f"Error saving file: {e}")
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    temp_dir = os.path.dirname(temp_file)
                    if temp_dir and os.path.exists(temp_dir):
                        try:
                            os.rmdir(temp_dir)
                        except OSError:
                            pass  # Directory not empty
            except Exception:
                pass  # Ignore cleanup errors
        
        self.temp_files.clear()
    
    def process_video(self, youtube_url: str, options: ProcessingOptions) -> Tuple[SubtitleInfo, Optional[str]]:
        """
        Process a YouTube video with the given options.
        
        Args:
            youtube_url: YouTube video URL
            options: Processing options
            
        Returns:
            Tuple of (SubtitleInfo, Optional[Gemini response])
        """
        try:
            # Download subtitles
            subtitle_info = self.download_subtitles(
                youtube_url, 
                options.language, 
                options.output_dir
            )
            
            # Process with Gemini if API key provided
            gemini_response = None
            if options.api_key:
                gemini_response = self.process_with_gemini(
                    subtitle_info.content,
                    options.api_key,
                    options.model
                )
            
            return subtitle_info, gemini_response
            
        except Exception as e:
            raise ValueError(f"Error processing video: {e}") 