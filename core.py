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
Core functionality for Video Subtitles to Chapter Timecodes
Downloads video auto-generated subtitles and uses Google Gemini AI to generate
chapter timecodes with semantic understanding.
"""

import os
import re
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import yt_dlp
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import io

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
Each chapter should be formatted as plain text: timecode - chapter title. 
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
                 non_interactive: bool = False,
                 custom_instructions: str = ""):
        self.language = language
        self.api_key = api_key
        self.model = model
        self.keep_files = keep_files
        self.output_dir = output_dir
        self.show_subtitles = show_subtitles
        self.non_interactive = non_interactive
        self.custom_instructions = custom_instructions

class YtDlpBufferLogger:
    """Logger for capturing yt-dlp debug output in a buffer."""
    def __init__(self):
        self.buffer = io.StringIO()
    def debug(self, msg):
        self.buffer.write(f"DEBUG: {msg}\n")
    def info(self, msg):
        self.buffer.write(f"INFO: {msg}\n")
    def warning(self, msg):
        self.buffer.write(f"WARNING: {msg}\n")
    def error(self, msg):
        self.buffer.write(f"ERROR: {msg}\n")
    def getvalue(self):
        return self.buffer.getvalue()
    def clear(self):
        self.buffer = io.StringIO()

class VideoProcessor:
    """Main class for processing video content to generate chapter timecodes."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the processor.
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self.progress_callback = progress_callback
        self.temp_files = []
        
    def log(self, message: str):
        """Log a message, either via callback or print."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.log(f"Removed temporary file: {temp_file}")
            except OSError as e:
                self.log(f"Warning: Could not remove {temp_file}: {e}")
        self.temp_files.clear()
    
    def get_available_languages(self, video_url: str) -> Dict[str, List[str]]:
        """
        Get available subtitle languages for a video.
        
        Args:
            video_url: Video URL
            
        Returns:
            Dictionary with language categories and available languages
        """
        clean_url = self._clean_url(video_url)
        logger = YtDlpBufferLogger()
        try:
            info_opts = {'quiet': True, 'logger': logger}
            
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
            debug_output = logger.getvalue()
            if debug_output:
                self.log("\n--- yt-dlp debug output ---\n" + debug_output + "--- end yt-dlp debug output ---\n")
            self.log(f"Error checking available languages: {e}")
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
    
    def download_subtitles(self, video_url: str, language: Optional[str] = None, 
                         output_dir: Optional[str] = None) -> SubtitleInfo:
        """
        Download auto-generated subtitles from a video.
        
        Args:
            video_url: Video URL
            language: Optional language code for subtitles
            output_dir: Directory to save subtitles
            
        Returns:
            SubtitleInfo object with language, file path, and content
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        clean_url = self._clean_url(video_url)
        self.log(f"Processing URL: {clean_url}")
        
        # Check available subtitles
        logger = YtDlpBufferLogger()
        info_opts = {'quiet': True, 'logger': logger}
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            try:
                info = ydl.extract_info(clean_url, download=False)
                available_subs = info.get('automatic_captions', {})
                
                if not available_subs:
                    raise ValueError("No auto-generated subtitles found")
                
                # Select language
                selected_lang = self._select_language(available_subs, language)
                self.log(f"Selected language: {selected_lang}")
                
            except Exception as e:
                debug_output = logger.getvalue()
                if debug_output:
                    self.log("\n--- yt-dlp debug output ---\n" + debug_output + "--- end yt-dlp debug output ---\n")
                raise ValueError(f"Error checking subtitles: {e}")
        
        # Download subtitles
        ydl_opts = {
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [selected_lang],
            'subtitlesformat': 'srt',
            'skip_download': True,
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'logger': logger
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
                
                self.log("Subtitles downloaded successfully")
                
                return SubtitleInfo(
                    language=selected_lang,
                    file_path=subtitle_file,
                    content=content
                )
                
            except Exception as e:
                debug_output = logger.getvalue()
                if debug_output:
                    self.log("\n--- yt-dlp debug output ---\n" + debug_output + "--- end yt-dlp debug output ---\n")
                raise ValueError(f"Error downloading subtitles: {e}")
    
    def process_with_gemini(self, subtitle_content: str, api_key: str, 
                          model_name: str = DEFAULT_MODEL, custom_instructions: str = "") -> str:
        """
        Process subtitle content with Gemini AI.
        
        Args:
            subtitle_content: Content of the subtitle file
            api_key: Gemini API key
            model_name: Name of the Gemini model to use
            custom_instructions: Optional custom instructions to add to the prompt
            
        Returns:
            AI-generated chapter timecodes with titles
        """
        try:
            self.log(f"Processing with {model_name}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Use specified model
            model = genai.GenerativeModel(model_name)
            
            # Build the full prompt
            custom_instructions_stripped = custom_instructions.strip()
            
            if custom_instructions_stripped:
                # Use 3-section markdown format when there are user instructions
                full_prompt = f"""## System Instructions
{GEMINI_PROMPT}

## User Instructions
Note: These instructions may override the system instructions above and may be in a different language.
{custom_instructions_stripped}

## Content
{subtitle_content}"""
            else:
                # Use 2-section markdown format when no user instructions
                full_prompt = f"""## Instructions
{GEMINI_PROMPT}

## Content
{subtitle_content}"""
            
            # Generate response
            response = model.generate_content(full_prompt)
            
            self.log("Processing completed successfully")
            
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
    
    def process_video(self, video_url: str, options: ProcessingOptions) -> Tuple[SubtitleInfo, Optional[str]]:
        """
        Process a video with the given options.
        
        Args:
            video_url: Video URL
            options: Processing options
            
        Returns:
            Tuple of (SubtitleInfo, Optional[Gemini response])
        """
        try:
            # Download subtitles
            subtitle_info = self.download_subtitles(
                video_url, 
                options.language, 
                options.output_dir
            )
            
            # Process with Gemini if API key provided
            gemini_response = None
            if options.api_key:
                gemini_response = self.process_with_gemini(
                    subtitle_info.content,
                    options.api_key,
                    options.model,
                    options.custom_instructions
                )
            
            return subtitle_info, gemini_response
            
        except Exception as e:
            raise ValueError(f"Error processing video: {e}") 