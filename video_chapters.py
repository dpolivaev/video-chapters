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
YouTube Subtitles to Chapter Timecodes
Downloads YouTube auto-generated subtitles and uses Google Gemini AI to generate 
chapter timecodes with descriptive titles for video content.
"""

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
import yt_dlp
import google.generativeai as genai

# ========================================
# MODEL SETTINGS (easy to edit)
# ========================================
DEFAULT_MODEL = 'gemini-2.5-pro'
AVAILABLE_MODELS = [
    'gemini-2.5-pro', 
    'gemini-2.5-flash'
]

def download_subtitles(youtube_url: str, language: str = None, output_dir: str = None) -> str:
    """
    Download auto-generated subtitles from YouTube video.
    
    Args:
        youtube_url: YouTube video URL
        language: Optional language code for subtitles (e.g., 'ru', 'en', 'es')
        output_dir: Directory to save subtitles (optional)
    
    Returns:
        Path to the downloaded subtitle file
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    
    # First, check what subtitles are available
    info_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(info_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            available_subs = info.get('automatic_captions', {})
            
            if not available_subs:
                print("❌ ERROR: No auto-generated subtitles found!")
                print("This video doesn't have auto-generated captions available.")
                sys.exit(1)
            
            # Language selection logic
            preferred_lang = None
            
            if language:
                # User specified a language - try to find it
                if language in available_subs:
                    preferred_lang = language
                    print(f"🎯 Found requested language: {language}")
                elif f"{language}-orig" in available_subs:
                    preferred_lang = f"{language}-orig"
                    print(f"🎯 Found requested language (original): {language}-orig")
                else:
                    print(f"❌ ERROR: Requested language '{language}' not found!")
                    print("Available subtitle languages:")
                    for lang in available_subs.keys():
                        print(f"  - {lang}")
                    print(f"\nTry one of the available languages above.")
                    sys.exit(1)
            else:
                # No language specified - use first available
                preferred_lang = list(available_subs.keys())[0]
                print(f"🎯 Auto-selected language: {preferred_lang}")
                if len(available_subs) > 1:
                    print("Available languages:", ", ".join(list(available_subs.keys())[:5]))
                    print("Use --language parameter to select a specific language.")
                
        except Exception as e:
            print(f"Error checking available subtitles: {e}")
            sys.exit(1)
    
    # Download the subtitles
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [preferred_lang],
        'subtitlesformat': 'srt',
        'skip_download': True,  # Don't download video, only subtitles
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Download subtitles
            ydl.download([youtube_url])
            
            # Find the downloaded subtitle file
            subtitle_files = list(Path(output_dir).glob('*.srt'))
            if not subtitle_files:
                raise FileNotFoundError("No subtitle files were downloaded")
            
            # Return the downloaded file
            subtitle_file = str(subtitle_files[0])
            print(f"✅ Downloaded subtitles")
            
            return subtitle_file
            
        except Exception as e:
            print(f"Error downloading subtitles: {e}")
            sys.exit(1)

def read_subtitle_file(file_path: str) -> str:
    """
    Read subtitle file content.
    
    Args:
        file_path: Path to the subtitle file
    
    Returns:
        Content of the subtitle file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading subtitle file: {e}")
        sys.exit(1)

def ask_user_choice(question: str) -> bool:
    """
    Ask user a yes/no question.
    
    Args:
        question: Question to ask
    
    Returns:
        True for yes, False for no
    """
    while True:
        answer = input(f"{question} (yes/no): ").strip().lower()
        if answer in ['yes', 'y', 'да', 'д', 'sí', 'si', 'oui', 'ja', 'tak']:
            return True
        elif answer in ['no', 'n', 'нет', 'н', 'non', 'nein', 'nie']:
            return False
        else:
            print("Please answer 'yes' or 'no'")

def send_to_gemini(subtitle_content: str, api_key: str, model_name: str = None) -> str:
    """
    Send subtitle content to Gemini AI to generate chapter timecodes.
    
    Args:
        subtitle_content: Content of the subtitle file
        api_key: Gemini API key
        model_name: Name of the Gemini model to use
    
    Returns:
        AI-generated chapter timecodes with titles
    """
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use default model if none specified
        if model_name is None:
            model_name = DEFAULT_MODEL
        
        # Use specified Gemini model
        model = genai.GenerativeModel(model_name)
        
        # Language-agnostic prompt - Gemini will detect language automatically
        prompt = "Break down this video content into chapters and generate timecodes in mm:ss format (e.g., 05:30, 12:45). Each chapter should start with time in mm:ss format - chapter title. Generate the chapter titles in the same language as the subtitles."
        
        # Combine prompt with subtitle content
        full_prompt = f"{prompt}\n\nSubtitles:\n{subtitle_content}"
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        return response.text
        
    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        sys.exit(1)

def main():
    """Main function to generate chapter timecodes from YouTube subtitles."""
    parser = argparse.ArgumentParser(
        description='Download YouTube subtitles and generate chapter timecodes with Gemini AI'
    )
    parser.add_argument('youtube_url', help='YouTube video URL')
    parser.add_argument('--language', '-l', help='Language code for subtitles (e.g., ru, en, es). If not specified, uses first available language.')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--keep-files', action='store_true', help='Keep downloaded subtitle files')
    parser.add_argument('--output-dir', help='Directory to save subtitle files')
    parser.add_argument('--show-subtitles', action='store_true', help='Show subtitle content before processing')
    parser.add_argument('--quiet', action='store_true', help='Run in non-interactive mode (auto-send to Gemini, don\'t save file)')
    parser.add_argument('--model', default=DEFAULT_MODEL, 
                       choices=AVAILABLE_MODELS,
                       help=f'Gemini model to use (default: {DEFAULT_MODEL})')
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please provide Gemini API key via --api-key argument or GEMINI_API_KEY environment variable")
        sys.exit(1)
    
    # Clean URL from shell escaping
    clean_url = args.youtube_url.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&')
    if clean_url != args.youtube_url:
        print(f"🔧 Fixed URL: {clean_url}")
    
    print(f"Processing YouTube URL: {clean_url}")
    
    # Download subtitles
    print("Downloading subtitles...")
    subtitle_file = download_subtitles(clean_url, args.language, args.output_dir)
    print(f"Subtitles downloaded to: {subtitle_file}")
    
    # Read subtitle content
    print("Reading subtitle content...")
    subtitle_content = read_subtitle_file(subtitle_file)
    
    # Show subtitle content if requested
    if args.show_subtitles:
        print("\n" + "="*50)
        print("SUBTITLE CONTENT:")
        print("="*50)
        print(subtitle_content)
        print("="*50)
        print()
    
    # Interactive or quiet mode
    if args.quiet:
        # Quiet mode: don't save file, auto-send to Gemini
        keep_file = False
        send_to_ai = True
        print("🤫 Quiet mode: automatically sending to Gemini...")
    else:
        # Interactive mode: ask user about saving first
        keep_file = ask_user_choice("💾 Save subtitle file?")
        
        # Save file immediately if requested
        if keep_file:
            # Move file to current directory with a nice name
            safe_filename = re.sub(r'[^\w\s-]', '', os.path.basename(subtitle_file)).strip()
            safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
            new_path = f"subtitles-{safe_filename}"
            
            shutil.copy2(subtitle_file, new_path)
            print(f"✅ File saved as: {new_path}")
            
            # Show first 10 lines of the saved file
            print("\n📄 First 10 lines of the file:")
            print("-" * 40)
            with open(new_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if i > 10:
                        break
                    print(f"{i:2d}: {line.rstrip()}")
            print("-" * 40)
        
        # Now ask about sending to Gemini
        send_to_ai = ask_user_choice("🤖 Send subtitles to Gemini for processing?")
    
    if send_to_ai:
        print(f"📤 Sending subtitles to {args.model}...")
        response = send_to_gemini(subtitle_content, api_key, args.model)
        
        # Output response
        print("\n" + "="*50)
        print("GEMINI RESPONSE:")
        print("="*50)
        print(response)
    else:
        print("⏭️  Skipping Gemini processing.")
    
    # Clean up temporary files unless user chose to keep them or specified output dir
    if not keep_file and not args.keep_files and args.output_dir is None:
        try:
            os.remove(subtitle_file)
            os.rmdir(os.path.dirname(subtitle_file))
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main() 