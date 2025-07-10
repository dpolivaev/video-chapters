#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller's built-in signing
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

def run_command(cmd, check=True, timeout=300):
    """Run a shell command and return success status."""
    print(f"▶️  {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        if check and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        if result.stdout:
            print(f"✅ {result.stdout}")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def find_signing_identity(name_or_identity):
    """Find the full signing identity from a partial name."""
    import subprocess
    
    # If it already looks like a full identity, use it as-is
    if name_or_identity.startswith("Developer ID Application:"):
        return name_or_identity
    
    # Search for matching identities
    try:
        result = subprocess.run(
            ["security", "find-identity", "-v", "-p", "codesigning"],
            capture_output=True, text=True, check=True, timeout=30
        )
        
        # Parse the output to find matching identity
        for line in result.stdout.split('\n'):
            if name_or_identity in line and "Developer ID Application:" in line:
                # Extract the identity string (everything in quotes)
                import re
                match = re.search(r'"([^"]*)"', line)
                if match:
                    full_identity = match.group(1)
                    print(f"🔍 Found signing identity: {full_identity}")
                    return full_identity
        
        print(f"❌ No signing identity found containing '{name_or_identity}'")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error searching for signing identity: {e}")
        return None

def notarize_macos_app(app_path, keychain_profile):
    """Notarize macOS app bundle using the modern approach."""
    print(f"🔔 Notarizing macOS app: {app_path}")
    
    # Create zip file for notarization using ditto
    zip_path = f"{app_path}.zip"
    
    print(f"📦 Creating zip file for notarization...")
    cmd = f'ditto -c -k --sequesterRsrc --keepParent "{app_path}" "{zip_path}"'
    if not run_command(cmd, timeout=300):
        print("❌ Failed to create zip file")
        return False
    
    # Submit for notarization with --wait flag
    print("🔔 Submitting for notarization...")
    cmd = f'xcrun notarytool submit "{zip_path}" --keychain-profile {keychain_profile} --wait'
    if not run_command(cmd, timeout=1800):  # 30 minutes timeout
        print("❌ Notarization failed")
        return False
    
    # Staple the notarization to the app bundle
    print(f"🔖 Stapling notarization to app bundle...")
    cmd = f'xcrun stapler staple "{app_path}"'
    if not run_command(cmd, timeout=60):
        print("❌ Failed to staple notarization")
        return False
    
    print("✅ Notarization completed successfully!")
    
    # Clean up zip file
    try:
        Path(zip_path).unlink()
        print("🧹 Cleaned up zip file")
    except Exception as e:
        print(f"⚠️  Could not remove zip file: {e}")
    
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
        run_command(cmd, timeout=30)
        
        # Create DMG
        cmd = f'hdiutil create -volname "Chapter Timecodes" -srcfolder "{temp_dir}" -ov -format UDZO "{dmg_path}"'
        if not run_command(cmd, timeout=600):
            print("❌ Failed to create DMG")
            return False
            
        print("✅ DMG created successfully")
        return True
        
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def sign_windows_exe(exe_path):
    """Sign Windows executable using codesign.bat."""
    print(f"🔐 Signing Windows exe: {exe_path}")
    
    # Use the codesign.bat script
    codesign_script = Path("codesign/codesign.bat")
    
    if not codesign_script.exists():
        print("❌ codesign.bat not found in codesign/ directory")
        return False
    
    # Run the codesign.bat script
    cmd = f'"{codesign_script.absolute()}"'
    
    if not run_command(cmd):
        print("❌ Failed to sign Windows executable")
        return False
        
    print("✅ Windows executable signed successfully")
    return True

def build_gui_app(args):
    """Build the GUI application using PyInstaller's built-in signing."""
    print("🚀 Building GUI application...")
    
    # Determine platform-specific settings
    if sys.platform == "darwin":  # macOS
        icon_flag = "--icon=icon.icns" if Path("icon.icns").exists() else ""
        app_name = "Chapter Timecodes"
    elif sys.platform == "win32":  # Windows
        icon_flag = "--icon=icon.ico" if Path("icon.ico").exists() else ""
        app_name = "Chapter Timecodes"
    else:  # Linux
        icon_flag = "--icon=icon.png" if Path("icon.png").exists() else ""
        app_name = "Chapter Timecodes"
    
    # Build command - use PyInstaller's built-in signing for macOS
    cmd = f'pyinstaller --onedir --windowed --name "{app_name}" {icon_flag} --add-data "LICENSE:."'
    
    # Add macOS signing parameters directly to PyInstaller
    if sys.platform == "darwin" and args.sign and args.signing_identity:
        full_identity = find_signing_identity(args.signing_identity)
        if not full_identity:
            print("❌ Could not find signing identity")
            return False
        
        print(f"🔐 Using PyInstaller built-in signing")
        cmd += f' --codesign-identity "{full_identity}"'
        
        # Add entitlements file
        if Path("entitlements.plist").exists():
            cmd += f' --osx-entitlements-file entitlements.plist'
        else:
            print("❌ entitlements.plist not found - required for macOS signing")
            return False
    
    cmd += ' gui.py'
    
    # PyInstaller can take a long time
    if not run_command(cmd, timeout=1800):
        print("❌ Failed to build GUI application")
        return False
    
    print("✅ GUI application built successfully!")
    
    # For macOS, verify the signing worked
    if sys.platform == "darwin" and args.sign:
        app_path = f"dist/{app_name}.app"
        
        print("🔍 Verifying signing...")
        cmd = f'codesign -vv --strict "{app_path}"'
        if not run_command(cmd, timeout=60):
            print("❌ Signing verification failed")
            return False
        print("✅ Signing verified successfully")
        
        # Notarize if profile provided
        if args.notary_profile:
            if not notarize_macos_app(app_path, args.notary_profile):
                return False
        
        # Create and sign DMG if requested
        if args.create_dmg:
            dmg_path = f"dist/{app_name}.dmg"
            
            if not create_dmg(app_path, dmg_path):
                return False
                
            # Sign the DMG file
            print(f"🔐 Signing DMG file...")
            cmd = f'codesign --sign "{full_identity}" "{dmg_path}"'
            if not run_command(cmd, timeout=120):
                print("❌ Failed to sign DMG")
                return False
            print("✅ DMG signed successfully")
                
    elif sys.platform == "win32" and args.sign:
        exe_path = f"dist/{app_name}.exe"
        
        if not sign_windows_exe(exe_path):
            return False
    
    return True

def clean_build_files():
    """Clean up all build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    paths_to_clean = ["build", "dist", "temp_dmg", "*.spec", "__pycache__", "*.pyc"]
    
    for pattern in paths_to_clean:
        if "*" in pattern:
            for path in Path(".").glob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
                except OSError:
                    pass
        else:
            path = Path(pattern)
            if path.exists():
                try:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
                except OSError:
                    pass
    
    print("✅ Cleanup complete")

def main():
    """Main build function."""
    print("🚀 Chapter Timecodes Build Script")
    
    parser = argparse.ArgumentParser(description="Build Chapter Timecodes executables")
    
    # Build options
    parser.add_argument("--gui-only", action="store_true", help="Build GUI application only (default)")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean up build files")
    
    # Signing options
    parser.add_argument("--sign", action="store_true", help="Enable code signing")
    parser.add_argument("--signing-identity", help="Code signing identity")
    parser.add_argument("--notary-profile", help="macOS notarization keychain profile")
    parser.add_argument("--create-dmg", action="store_true", help="Create DMG package (macOS)")
    
    # Windows signing options (certificate info is configured in codesign/codesign.bat)
    
    args = parser.parse_args()
    
    # Validate signing requirements
    if args.sign and sys.platform == "darwin" and not args.signing_identity:
        print("❌ --signing-identity required for macOS code signing")
        sys.exit(1)
    
    # Clean up before building
    if not args.no_clean:
        clean_build_files()
    
    # Build application
    if not build_gui_app(args):
        print("❌ Build failed!")
        sys.exit(1)
    
    print("✅ Build completed successfully!")

if __name__ == "__main__":
    main() 