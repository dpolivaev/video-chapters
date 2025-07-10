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
Video Subtitles to Chapter Timecodes (CLI version)
Downloads video auto-generated subtitles and uses Google Gemini AI to generate
chapter timecodes with semantic understanding.

This is the command-line interface for the timecode generator.
For GUI version, use gui.py instead.

Example usage:
    python video_chapters.py "https://www.youtube.com/watch?v=VIDEO_ID" --api-key YOUR_API_KEY
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from core import VideoProcessor, ProcessingOptions, DEFAULT_MODEL, AVAILABLE_MODELS
from config import config

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

def show_available_languages(processor: VideoProcessor, url: str):
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
    """Main function to generate chapter timecodes from video subtitles."""
    parser = argparse.ArgumentParser(
        description='Download video subtitles and generate chapter timecodes with Gemini AI'
    )
    parser.add_argument('video_url', help='Video URL (supports YouTube and other platforms)')
    parser.add_argument('--api-key', help='Google Gemini API key')
    parser.add_argument('--language', help='Subtitle language code (optional)')
    parser.add_argument('--model', choices=AVAILABLE_MODELS, default=DEFAULT_MODEL,
                       help=f'Gemini model to use (default: {DEFAULT_MODEL})')
    parser.add_argument('--keep-files', action='store_true', 
                       help='Keep downloaded subtitle files')
    parser.add_argument('--show-subtitles', action='store_true', 
                       help='Display downloaded subtitles')
    parser.add_argument('--output-dir', help='Output directory for files')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without user prompts')
    parser.add_argument('--check-languages', action='store_true',
                       help='Only check available languages, do not process')
    
    args = parser.parse_args()
    
    # Clean URL (handle shell escaping)
    clean_url = args.video_url.replace('\\?', '?').replace('\\=', '=').replace('\\&', '&')
    if clean_url != args.video_url:
        print(f"Cleaned URL: {clean_url}")
    
    print(f"Processing video URL: {clean_url}")
    
    # Create processor
    processor = VideoProcessor()
    
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
        non_interactive=args.non_interactive
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
        
        # Interactive or non-interactive mode
        if args.non_interactive:
            # Non-interactive mode: don't save file, auto-send to Gemini
            keep_file = False
            send_to_ai = True
            print("🤖 Non-interactive mode: automatically processed with Gemini...")
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
                safe_filename = os.path.basename(subtitle_info.file_path).strip()
                safe_filename = os.path.splitext(safe_filename)[0] # Remove .txt extension
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
            if not args.non_interactive:
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
                    safe_filename = os.path.basename(subtitle_info.file_path).strip()
                    safe_filename = os.path.splitext(safe_filename)[0] # Remove .txt extension
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