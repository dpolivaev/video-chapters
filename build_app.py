#!/usr/bin/env python3
"""
Build script for creating standalone executables
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    if result.stdout:
        print(f"Output: {result.stdout}")
    return True

def sign_macos_app(app_path, signing_identity=None):
    """Sign macOS application."""
    if not signing_identity:
        print("⚠️  No signing identity provided, skipping code signing")
        return True
        
    print(f"🔐 Signing macOS app: {app_path}")
    
    # Sign the app bundle
    cmd = f'codesign --force --verify --verbose --sign "{signing_identity}" "{app_path}"'
    if not run_command(cmd):
        print("❌ Failed to sign macOS app")
        return False
        
    # Verify signature
    cmd = f'codesign --verify --verbose=2 "{app_path}"'
    if not run_command(cmd):
        print("❌ Failed to verify signature")
        return False
        
    print("✅ macOS app signed successfully")
    return True

def create_dmg(app_path, dmg_path):
    """Create DMG file for macOS app."""
    print(f"📦 Creating DMG: {dmg_path}")
    
    # Create temporary directory for DMG contents
    temp_dir = Path("temp_dmg")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Copy app to temp directory
        app_name = Path(app_path).name
        temp_app_path = temp_dir / app_name
        shutil.copytree(app_path, temp_app_path)
        
        # Create symlink to Applications
        applications_link = temp_dir / "Applications"
        cmd = f'ln -sf /Applications "{applications_link}"'
        run_command(cmd)
        
        # Create DMG
        cmd = f'hdiutil create -volname "YouTube Chapters" -srcfolder "{temp_dir}" -ov -format UDZO "{dmg_path}"'
        if not run_command(cmd):
            print("❌ Failed to create DMG")
            return False
            
        print("✅ DMG created successfully")
        return True
        
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def notarize_macos_dmg(dmg_path, keychain_profile):
    """Notarize macOS DMG."""
    print(f"🔔 Notarizing DMG: {dmg_path}")
    
    # Submit for notarization
    cmd = f'xcrun notarytool submit "{dmg_path}" --keychain-profile {keychain_profile} --wait'
    if not run_command(cmd):
        print("❌ Failed to notarize DMG")
        return False
        
    # Staple the notarization
    cmd = f'xcrun stapler staple "{dmg_path}"'
    if not run_command(cmd):
        print("❌ Failed to staple notarization")
        return False
        
    print("✅ DMG notarized successfully")
    return True

def sign_windows_exe(exe_path, cert_path=None, cert_password=None, timestamp_url=None):
    """Sign Windows executable."""
    if not cert_path:
        print("⚠️  No certificate provided, skipping code signing")
        return True
        
    print(f"🔐 Signing Windows exe: {exe_path}")
    
    # Build signtool command
    cmd = f'signtool.exe sign'
    
    if cert_path:
        cmd += f' /f "{cert_path}"'
    
    if cert_password:
        cmd += f' /p "{cert_password}"'
    
    if timestamp_url:
        cmd += f' /t "{timestamp_url}"'
    else:
        # Default timestamp server
        cmd += ' /t "http://timestamp.sectigo.com"'
    
    cmd += f' /v "{exe_path}"'
    
    if not run_command(cmd):
        print("❌ Failed to sign Windows executable")
        return False
        
    print("✅ Windows executable signed successfully")
    return True

def build_gui_app(args):
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
    
    # Handle platform-specific signing and packaging
    if sys.platform == "darwin" and args.sign:
        app_path = f"dist/{app_name}.app"
        
        # Sign the app
        if not sign_macos_app(app_path, args.signing_identity):
            return False
            
        # Create and sign DMG if requested
        if args.create_dmg:
            dmg_path = f"dist/{app_name}.dmg"
            
            if not create_dmg(app_path, dmg_path):
                return False
                
            # Sign the DMG
            if not sign_macos_app(dmg_path, args.signing_identity):
                return False
                
            # Notarize if profile provided
            if args.notary_profile:
                if not notarize_macos_dmg(dmg_path, args.notary_profile):
                    return False
                    
    elif sys.platform == "win32" and args.sign:
        exe_path = f"dist/{app_name}.exe"
        
        if not sign_windows_exe(exe_path, args.cert_path, args.cert_password, args.timestamp_url):
            return False
    
    return True

def build_cli_app(args):
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
    
    # Handle platform-specific signing
    if sys.platform == "darwin" and args.sign:
        app_path = f"dist/{app_name}"
        
        if not sign_macos_app(app_path, args.signing_identity):
            return False
            
    elif sys.platform == "win32" and args.sign:
        exe_path = f"dist/{app_name}.exe"
        
        if not sign_windows_exe(exe_path, args.cert_path, args.cert_password, args.timestamp_url):
            return False
    
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
    parser = argparse.ArgumentParser(description="Build YouTube Chapters executables")
    
    # Build options
    parser.add_argument("--gui-only", action="store_true", help="Build GUI application only")
    parser.add_argument("--cli-only", action="store_true", help="Build CLI application only")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean up build files")
    
    # Signing options
    parser.add_argument("--sign", action="store_true", help="Enable code signing")
    
    # macOS signing options
    parser.add_argument("--signing-identity", help="macOS code signing identity")
    parser.add_argument("--notary-profile", help="macOS notarization keychain profile")
    parser.add_argument("--create-dmg", action="store_true", help="Create DMG package (macOS)")
    
    # Windows signing options
    parser.add_argument("--cert-path", help="Windows certificate file path")
    parser.add_argument("--cert-password", help="Windows certificate password")
    parser.add_argument("--timestamp-url", help="Timestamp server URL")
    
    args = parser.parse_args()
    
    print("YouTube Chapters - Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is available
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller not found. Please install development requirements first:")
        print("pip install -r requirements-dev.txt")
        sys.exit(1)
    
    # Validate signing requirements
    if args.sign:
        if sys.platform == "darwin":
            if not args.signing_identity:
                print("Error: --signing-identity required for macOS code signing")
                sys.exit(1)
            
            # Check if codesign is available
            try:
                subprocess.run(["codesign", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: codesign not found. Make sure Xcode Command Line Tools are installed.")
                sys.exit(1)
                
            # Check notarization requirements
            if args.notary_profile:
                try:
                    subprocess.run(["xcrun", "notarytool", "--version"], check=True, capture_output=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("Error: notarytool not found. Make sure Xcode Command Line Tools are installed.")
                    sys.exit(1)
                    
        elif sys.platform == "win32":
            if not args.cert_path:
                print("Error: --cert-path required for Windows code signing")
                sys.exit(1)
                
            # Check if signtool is available
            try:
                subprocess.run(["signtool.exe"], check=False, capture_output=True)
            except FileNotFoundError:
                print("Error: signtool.exe not found. Make sure Windows SDK is installed.")
                sys.exit(1)
    
    # Determine what to build
    build_gui = not args.cli_only
    build_cli = not args.gui_only
    clean_after = not args.no_clean
    
    # Build applications
    success = True
    
    if build_gui:
        if not build_gui_app(args):
            success = False
    
    if build_cli:
        if not build_cli_app(args):
            success = False
    
    # Clean up
    if clean_after:
        clean_build_files()
    
    # Report results
    print("\n" + "=" * 40)
    if success:
        print("Build completed successfully!")
        if args.sign:
            print("🔐 Applications signed successfully!")
        if args.notary_profile and sys.platform == "darwin":
            print("🔔 macOS applications notarized successfully!")
        print("Check the 'dist' directory for your executables.")
        
        # List created files
        if Path("dist").exists():
            print("\nCreated files:")
            for file in Path("dist").iterdir():
                size = file.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"  - {file.name} ({size:.1f} MB)")
    else:
        print("Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 