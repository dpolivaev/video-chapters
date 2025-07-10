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
YouTube Subtitles to Chapter Timecodes (CLI version)
Downloads YouTube auto-generated subtitles and uses Google Gemini AI to generate 
chapter timecodes with descriptive titles for video content.
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

from core import YouTubeProcessor, ProcessingOptions, DEFAULT_MODEL, AVAILABLE_MODELS

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

def show_available_languages(processor: YouTubeProcessor, url: str):
    """Show available languages for the video."""
    try:
        langs = processor.get_available_languages(url)
        
        if not langs:
            print("❌ No subtitles available for this video.")
            return
        
        print("Available languages:")
        for category, languages in langs.items():
            if languages:
                print(f"  {category.title()}: {', '.join(languages)}")
        
        print("Use --language parameter to select a specific language.")
        
    except Exception as e:
        print(f"Error checking languages: {e}")

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
    parser.add_argument('--check-languages', action='store_true', help='Check available languages and exit')
    
    args = parser.parse_args()
    
    # Clean URL from shell escaping
    clean_url = args.youtube_url.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&')
    if clean_url != args.youtube_url:
        print(f"🔧 Fixed URL: {clean_url}")
    
    print(f"Processing YouTube URL: {clean_url}")
    
    # Create processor
    processor = YouTubeProcessor()
    
    # Check languages only if requested
    if args.check_languages:
        show_available_languages(processor, clean_url)
        return
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: Please provide Gemini API key via --api-key argument or GEMINI_API_KEY environment variable")
        sys.exit(1)
    
    # Create processing options
    options = ProcessingOptions(
        language=args.language,
        api_key=api_key,
        model=args.model,
        keep_files=args.keep_files,
        output_dir=args.output_dir,
        show_subtitles=args.show_subtitles,
        quiet=args.quiet
    )
    
    try:
        # Process video
        print("Processing video...")
        subtitle_info, gemini_response = processor.process_video(clean_url, options)
        
        # Show subtitle content if requested
        if args.show_subtitles:
            print("\n" + "="*50)
            print("SUBTITLE CONTENT:")
            print("="*50)
            print(subtitle_info.content)
            print("="*50)
            print()
        
        # Interactive or quiet mode
        if args.quiet:
            # Quiet mode: don't save file, auto-send to Gemini
            keep_file = False
            send_to_ai = True
            print("🤫 Quiet mode: automatically processed with Gemini...")
        else:
            # Interactive mode: show first 10 lines, then ask user about saving
            
            # Show first 10 lines of the subtitle content
            print("\n📄 First 10 lines of subtitles:")
            print("-" * 40)
            lines = subtitle_info.content.split('\n')
            for i, line in enumerate(lines[:10], 1):
                print(f"{i:2d}: {line}")
            if len(lines) > 10:
                print(f"... ({len(lines) - 10} more lines)")
            print("-" * 40)
            
            keep_file = ask_user_choice("💾 Save subtitle file?")
            
            # Save file immediately if requested
            if keep_file:
                # Save with a nice name and .txt extension
                safe_filename = re.sub(r'[^\w\s-]', '', os.path.basename(subtitle_info.file_path)).strip()
                safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
                new_path = f"subtitles-{safe_filename}.txt"
                
                shutil.copy2(subtitle_info.file_path, new_path)
                print(f"✅ File saved as: {new_path}")
        
        # Show Gemini response
        if gemini_response:
            print("\n" + "="*50)
            print("GEMINI RESPONSE:")
            print("="*50)
            print(gemini_response)
            
            # In interactive mode, offer to save the response
            if not args.quiet:
                print("\n📄 First 10 lines of Gemini response:")
                print("-" * 40)
                response_lines = gemini_response.split('\n')
                for i, line in enumerate(response_lines[:10], 1):
                    print(f"{i:2d}: {line}")
                if len(response_lines) > 10:
                    print(f"... ({len(response_lines) - 10} more lines)")
                print("-" * 40)
                
                save_response = ask_user_choice("💾 Save Gemini response?")
                if save_response:
                    # Create a filename based on the original video
                    safe_filename = re.sub(r'[^\w\s-]', '', os.path.basename(subtitle_info.file_path)).strip()
                    safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
                    response_path = f"chapters-{safe_filename}.txt"
                    
                    with open(response_path, 'w', encoding='utf-8') as f:
                        f.write(gemini_response)
                    print(f"✅ Gemini response saved as: {response_path}")
        else:
            print("⏭️  No Gemini processing performed.")
        
        print("\n✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary files
        if not args.keep_files:
            processor.cleanup()

if __name__ == "__main__":
    main() 