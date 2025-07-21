#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller's built-in signing
"""

import os
import sys
import subprocess
import shutil
import argparse
import platform
from pathlib import Path
from config import APP_VERSION

def run_command(cmd, check=True, timeout=300, env=None, interactive=False):
    """Run a shell command and return success status."""
    print(f"▶️  {cmd}")
    try:
        if interactive:
            # Run interactively for commands that need real-time output
            result = subprocess.run(
                cmd, 
                shell=True, 
                timeout=timeout,
                env=env
            )
        else:
            # Capture output for regular commands
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                env=env
            )
            
            if check and result.returncode != 0:
                print(f"❌ Error: {result.stderr}")
                return False
            if result.stdout:
                print(f"✅ {result.stdout}")
        
        return result.returncode == 0
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

def notarize_macos_dmg(dmg_path, keychain_profile):
    """Notarize macOS DMG file using the modern approach."""
    print(f"🔔 Notarizing macOS DMG: {dmg_path}")
    
    # Submit DMG for notarization with --wait flag
    print("🔔 Submitting DMG for notarization...")
    cmd = f'xcrun notarytool submit "{dmg_path}" --keychain-profile {keychain_profile} --wait'
    if not run_command(cmd, timeout=1800, interactive=True):  # 30 minutes timeout, interactive
        print("❌ Notarization failed")
        return False
    
    # Staple the notarization to the DMG
    print(f"🔖 Stapling notarization to DMG...")
    cmd = f'xcrun stapler staple "{dmg_path}"'
    if not run_command(cmd, timeout=60, interactive=True):
        print("❌ Failed to staple notarization")
        return False
    
    print("✅ DMG notarization completed successfully!")
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
    
    if not run_command(cmd, interactive=True):
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
    
    # Determine platform-specific settings and prepare all variable elements
    build_dir = Path("build")
    dist_path = "dist"
    work_path = "build/pyiwork"
    app_name = "Chapter Timecodes"
    icon_flag = ""
    extra_flags = []

    if sys.platform == "darwin":
        icon_path = build_dir / "icon.icns"
        if icon_path.exists():
            icon_flag = f"--icon={icon_path}"
        if args.sign and args.signing_identity:
            full_identity = find_signing_identity(args.signing_identity)
            if not full_identity:
                print("❌ Could not find signing identity")
                return False
            print(f"🔐 Using PyInstaller built-in signing")
            extra_flags.append(f'--codesign-identity "{full_identity}"')
            if Path("entitlements.plist").exists():
                extra_flags.append('--osx-entitlements-file entitlements.plist')
            else:
                print("❌ entitlements.plist not found - required for macOS signing")
                return False
    elif sys.platform == "win32":
        icon_path = build_dir / "icon.ico"
        if icon_path.exists():
            icon_flag = f"--icon={icon_path.absolute()}"
    else:
        icon_path = build_dir / "icon.png"
        if icon_path.exists():
            icon_flag = f"--icon={icon_path}"

    # Construct the full PyInstaller command as a single string
    cmd = (
        f'pyinstaller --onedir --windowed --name "{app_name}" {icon_flag} '
        f'--add-data "LICENSE:." --distpath "{dist_path}" --workpath "{work_path}" '
        f'{" ".join(extra_flags)} gui.py'
    )
    
    if sys.platform == "win32":
        # --- Windows directory build ---
        build_root = Path("build/winapp")
        app_dir = build_root / app_name
        dist_dir = Path("dist")
        dist_dir.mkdir(exist_ok=True)
        # Clean up previous build
        if build_root.exists():
            shutil.rmtree(build_root)
        # PyInstaller --onedir output to build/winapp/Chapter Timecodes
        icon_path = build_dir / "icon.ico"
        icon_flag = f"--icon={icon_path.absolute()}" if icon_path.exists() else ""
        cmd = (
            f'pyinstaller --onedir --windowed --name "{app_name}" {icon_flag} '
            f'--add-data "LICENSE:." '
            f'--distpath "{build_root}" --workpath "build/pyiwork" gui.py'
        )
        if not run_command(cmd, timeout=1800):
            print("❌ Failed to build GUI application")
            return False
        # Sign the exe if requested
        exe_path = app_dir / f"{app_name}.exe"
        if args.sign:
            if not sign_windows_exe(exe_path):
                return False
        # Zip the Chapter Timecodes folder into dist/ as ChapterTimecodes-v{APP_VERSION}.zip
        zip_name = f"ChapterTimecodes-v{APP_VERSION}-windows.zip"
        zip_path = dist_dir / zip_name
        # Remove existing zip if present
        if zip_path.exists():
            zip_path.unlink()
        # Zip the folder so that Chapter Timecodes/ is the root in the zip
        import zipfile
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = Path(root) / file
                    # arcname ensures Chapter Timecodes/ is the root in the zip
                    arcname = str(file_path.relative_to(build_root))
                    zipf.write(file_path, arcname)
        print(f"✅ Created {zip_path}")
        return True
    
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
        
        # Create DMG if requested or if notarization is requested
        if args.create_dmg or args.notary_profile:
            dmg_path = f"dist/{app_name}.dmg"
            
            if not create_dmg(app_path, dmg_path):
                return False
                
            # Get architecture for DMG name
            arch = platform.machine()
            if arch == "x86_64":
                arch_suffix = "x64"
            elif arch == "arm64":
                arch_suffix = "arm64"
            else:
                arch_suffix = arch
            
            # Rename DMG to versioned name
            versioned_dmg = f"dist/ChapterTimecodes-v{APP_VERSION}-{arch_suffix}.dmg"
            Path(dmg_path).rename(versioned_dmg)
            print(f"✅ Renamed DMG to: {versioned_dmg}")
                
            # Sign the DMG file with versioned name if signing is enabled
            if args.sign:
                print(f"🔐 Signing DMG file...")
                cmd = f'codesign --sign "{full_identity}" "{versioned_dmg}"'
                if not run_command(cmd, timeout=120):
                    print("❌ Failed to sign DMG")
                    return False
                print("✅ DMG signed successfully")
            
            # Notarize DMG if profile provided
            if args.notary_profile:
                if not notarize_macos_dmg(versioned_dmg, args.notary_profile):
                    return False
    
    elif sys.platform == "win32" and args.sign:
        exe_path = f"dist/{app_name}.exe"
        
        if not sign_windows_exe(exe_path):
            return False
    
    # Rename final outputs to include version
    if sys.platform == "win32":
        original_exe = f"dist/{app_name}.exe"
        versioned_exe = f"dist/ChapterTimecodes-v{APP_VERSION}.exe"
        if Path(original_exe).exists():
            Path(original_exe).rename(versioned_exe)
            print(f"✅ Renamed to: {versioned_exe}")
    elif sys.platform == "darwin" and (args.create_dmg or args.notary_profile) and not args.sign:
        # Handle DMG renaming when not signing
        original_dmg = f"dist/{app_name}.dmg"
        if Path(original_dmg).exists():
            arch = platform.machine()
            if arch == "x86_64":
                arch_suffix = "x64"
            elif arch == "arm64":
                arch_suffix = "arm64"
            else:
                arch_suffix = arch
            
            versioned_dmg = f"dist/ChapterTimecodes-v{APP_VERSION}-{arch_suffix}.dmg"
            Path(original_dmg).rename(versioned_dmg)
            print(f"✅ Renamed DMG to: {versioned_dmg}")
            
            # Notarize DMG if profile provided but no signing
            if args.notary_profile:
                if not notarize_macos_dmg(versioned_dmg, args.notary_profile):
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
        parser.add_argument("--notary-profile", help="macOS notarization keychain profile (automatically creates DMG)")
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