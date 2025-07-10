#!/usr/bin/env python3
"""
Build script for creating standalone executables
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def build_gui_app():
    """Build the GUI application."""
    print("Building GUI application...")
    
    # Determine platform-specific settings
    if sys.platform == "darwin":  # macOS
        icon_flag = "--icon=icon.icns" if Path("icon.icns").exists() else ""
        app_name = "YouTube Chapters"
    elif sys.platform == "win32":  # Windows
        icon_flag = "--icon=icon.ico" if Path("icon.ico").exists() else ""
        app_name = "YouTube Chapters"
    else:  # Linux
        icon_flag = "--icon=icon.png" if Path("icon.png").exists() else ""
        app_name = "YouTube Chapters"
    
    # Build command
    cmd = f'pyinstaller --onefile --windowed --name "{app_name}" {icon_flag} --add-data "LICENSE:." gui.py'
    
    if not run_command(cmd):
        print("Failed to build GUI application")
        return False
    
    print("GUI application built successfully!")
    return True

def build_cli_app():
    """Build the CLI application."""
    print("Building CLI application...")
    
    # Determine platform-specific settings
    if sys.platform == "darwin":  # macOS
        app_name = "youtube-chapters-cli"
    elif sys.platform == "win32":  # Windows
        app_name = "youtube-chapters-cli"
    else:  # Linux
        app_name = "youtube-chapters-cli"
    
    # Build command
    cmd = f'pyinstaller --onefile --name "{app_name}" --add-data "LICENSE:." video_chapters.py'
    
    if not run_command(cmd):
        print("Failed to build CLI application")
        return False
    
    print("CLI application built successfully!")
    return True

def clean_build_files():
    """Clean up PyInstaller build files."""
    print("Cleaning up build files...")
    
    # Remove build directory
    if Path("build").exists():
        shutil.rmtree("build")
        print("Removed build directory")
    
    # Remove spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"Removed {spec_file}")
    
    print("Cleanup complete!")

def main():
    """Main build function."""
    print("YouTube Chapters - Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is available
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller not found. Please install development requirements first:")
        print("pip install -r requirements-dev.txt")
        sys.exit(1)
    
    # Parse arguments
    build_gui = True
    build_cli = True
    clean_after = True
    
    if len(sys.argv) > 1:
        if "--gui-only" in sys.argv:
            build_cli = False
        elif "--cli-only" in sys.argv:
            build_gui = False
        if "--no-clean" in sys.argv:
            clean_after = False
    
    # Build applications
    success = True
    
    if build_gui:
        if not build_gui_app():
            success = False
    
    if build_cli:
        if not build_cli_app():
            success = False
    
    # Clean up
    if clean_after:
        clean_build_files()
    
    # Report results
    print("\n" + "=" * 40)
    if success:
        print("Build completed successfully!")
        print("Check the 'dist' directory for your executables.")
        
        # List created files
        if Path("dist").exists():
            print("\nCreated files:")
            for file in Path("dist").iterdir():
                print(f"  - {file.name}")
    else:
        print("Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 