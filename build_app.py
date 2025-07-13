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
        # Copy app to temp directory using ditto to preserve extended attributes
        app_name = Path(app_path).name
        temp_app_path = temp_dir / app_name
        cmd = f'ditto "{app_path}" "{temp_app_path}"'
        if not run_command(cmd, timeout=120):
            print("❌ Failed to copy app bundle")
            return False
        
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

def generate_platform_icons():
    """Generate platform-specific icons from high-resolution source."""
    print("🎨 Generating platform-specific icons...")
    
    # Ensure build directory exists
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    # Check if we have the high-resolution source
    highres_png = Path("icon_highres.png")
    if not highres_png.exists():
        print("⚠️  icon_highres.png not found - creating from icon.png")
        if not Path("icon.png").exists():
            print("❌ No icon source files found")
            return False
        
        # If we only have the low-res PNG, use it as source
        # This is a fallback for systems without the high-res version
        highres_png = Path("icon.png")
    
    try:
        # Import PIL for icon generation
        from PIL import Image
        
        # Load the source icon
        base_icon = Image.open(highres_png)
        base_size = base_icon.size[0]
        print(f"📊 Using source icon: {highres_png} ({base_size}x{base_size})")
        
        if sys.platform == "darwin":
            # macOS - create .icns using iconutil
            print("🍎 Creating macOS .icns file...")
            
            # Create iconset directory in build folder
            iconset_dir = build_dir / "icon.iconset"
            iconset_dir.mkdir(exist_ok=True)
            
            # Define required sizes for macOS
            sizes = [
                (16, 'icon_16x16.png'),
                (32, 'icon_16x16@2x.png'),
                (32, 'icon_32x32.png'),
                (64, 'icon_32x32@2x.png'),
                (128, 'icon_128x128.png'),
                (256, 'icon_128x128@2x.png'),
                (256, 'icon_256x256.png'),
                (512, 'icon_256x256@2x.png'),
                (512, 'icon_512x512.png'),
                (1024, 'icon_512x512@2x.png') if base_size >= 1024 else None
            ]
            
            # Filter out None entries
            sizes = [s for s in sizes if s is not None]
            
            # Create all required sizes in build directory
            for size, filename in sizes:
                if size <= base_size:
                    resized = base_icon.resize((size, size), Image.LANCZOS)
                    resized.save(iconset_dir / filename, 'PNG', optimize=True)
                else:
                    print(f"⚠️  Skipping {filename} - source too small ({base_size}x{base_size})")
            
            # Convert to .icns using iconutil (output to build directory)
            icns_path = build_dir / "icon.icns"
            if shutil.which("iconutil"):
                if run_command(f"iconutil -c icns '{iconset_dir}' -o '{icns_path}'"):
                    print(f"✅ Created {icns_path}")
                    # Clean up iconset directory
                    shutil.rmtree(iconset_dir)
                else:
                    print("❌ Failed to create .icns file")
                    return False
            else:
                print("⚠️  iconutil not available - keeping PNG fallback")
                
        elif sys.platform == "win32":
            # Windows - create .ico file
            print("🪟 Creating Windows .ico file...")
            
            # Create multiple sizes for ICO
            ico_sizes = [16, 32, 48, 64, 128, 256]
            icons = []
            
            for size in ico_sizes:
                if size <= base_size:
                    icon = base_icon.resize((size, size), Image.LANCZOS)
                    icons.append(icon)
            
            if icons:
                # Save ICO file to build directory
                ico_path = build_dir / "icon.ico"
                icons[0].save(ico_path, format='ICO', 
                             sizes=[(icon.size[0], icon.size[1]) for icon in icons])
                print(f"✅ Created {ico_path} with {len(icons)} sizes")
            else:
                print("❌ No suitable sizes for ICO creation")
                return False
                
        else:
            # Linux and other platforms - use PNG
            print("🐧 Using PNG icon for Linux/other platforms...")
            
        # Always create/update the standard PNG icon in build directory
        png_path = build_dir / "icon.png"
        if base_size > 64:
            standard_png = base_icon.resize((64, 64), Image.LANCZOS)
            standard_png.save(png_path, 'PNG', optimize=True)
            print(f"✅ Created/updated {png_path} (64x64)")
        else:
            # Copy existing icon if it's already the right size
            base_icon.save(png_path, 'PNG', optimize=True)
            print(f"✅ Copied {png_path} (64x64)")
        
        return True
        
    except ImportError:
        print("❌ PIL/Pillow not installed - cannot generate icons")
        print("   Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ Error generating icons: {e}")
        return False

def build_gui_app(args):
    """Build the GUI application using PyInstaller's built-in signing."""
    print("🚀 Building GUI application...")
    
    # Generate platform-specific icons first
    if not generate_platform_icons():
        print("⚠️  Icon generation failed - continuing without icons")
    
    # Determine platform-specific settings
    build_dir = Path("build")
    if sys.platform == "darwin":  # macOS
        icon_path = build_dir / "icon.icns"
        icon_flag = f"--icon={icon_path}" if icon_path.exists() else ""
        app_name = "Chapter Timecodes"
    elif sys.platform == "win32":  # Windows
        icon_path = build_dir / "icon.ico"
        icon_flag = f"--icon={icon_path}" if icon_path.exists() else ""
        app_name = "Chapter Timecodes"
    else:  # Linux
        icon_path = build_dir / "icon.png"
        icon_flag = f"--icon={icon_path}" if icon_path.exists() else ""
        app_name = "Chapter Timecodes"
    
    # Build command - use PyInstaller's built-in signing for macOS
    # Use --onefile for Windows/Linux to avoid subdirectory, --onedir for macOS for better performance
    if sys.platform == "darwin":
        # macOS uses --onedir which handles local modules better
        cmd = f'pyinstaller --onedir --windowed --name "{app_name}" {icon_flag} --add-data "LICENSE:."'
    else:
        # Windows/Linux use --onefile which needs explicit module inclusion
        cmd = f'pyinstaller --onefile --windowed --name "{app_name}" {icon_flag} --add-data "LICENSE:." --add-data "config.py:." --add-data "core.py:."'
    
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
    parser.add_argument("--sign", action="store_true", help="Enable code signing (macOS only)")
    if sys.platform == "darwin":
        parser.add_argument("--signing-identity", help="Code signing identity (macOS only)")
        parser.add_argument("--notary-profile", help="macOS notarization keychain profile")
        parser.add_argument("--create-dmg", action="store_true", help="Create DMG package (macOS only)")
    
    # Windows signing options (certificate info is configured in codesign/codesign.bat)
    
    args = parser.parse_args()
    
    # Validate signing requirements (macOS only)
    if sys.platform == "darwin" and args.sign and not args.signing_identity:
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