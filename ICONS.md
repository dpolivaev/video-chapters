# Icon System for Chapter Timecodes

This document explains the cross-platform icon system for the Chapter Timecodes application.

## 📁 Files to Commit to Git

**Always commit these source files:**
- `icon_highres.png` (8.6 KB) - High-resolution source (1024×1024)

**Do NOT commit these generated files:**
- `build/` directory - Contains ALL temporary and generated files during build
  - `build/icon.icns` - macOS icon (generated during build)
  - `build/icon.ico` - Windows icon (generated during build)  
  - `build/icon.png` - Standard fallback (generated during build)

## 🔧 How It Works

### Build Process
1. **Source Files**: The build script uses `icon_highres.png` as the primary source
2. **Platform Detection**: Automatically detects the operating system
3. **Temporary Files**: Creates temporary files in `build/` directory
4. **Icon Generation**: Creates platform-specific icons during build

### Platform-Specific Generation

#### macOS (requires iconutil)
- Creates `build/icon.iconset/` directory with 10 different sizes
- Uses `iconutil -c icns build/icon.iconset -o icon.icns` to generate `icon.icns`
- Cleans up temporary iconset directory in build folder
- Result: ~140 KB `.icns` file with crisp icons at all sizes

#### Windows (requires PIL/Pillow)
- Creates `.ico` file with 6 different sizes (16×16 to 256×256)
- Uses PIL to generate multi-size ICO format
- Result: ~4 KB `.ico` file

#### Linux/Other
- Uses `icon.png` directly (64×64)
- No additional generation needed

## 🎨 Icon Design

The current icon features:
- **Blue circular background** (#4A90E2)
- **White play triangle** (video symbol)
- **Chapter marks** (small white lines indicating timecodes)
- **Transparent background** for OS integration

## 🚀 Usage in Build Script

The `build_app.py` script automatically:
1. Calls `generate_platform_icons()` before building
2. Detects available tools (iconutil, PIL)
3. Creates appropriate platform-specific icons
4. Includes them in the PyInstaller build

## 📝 Customizing Icons

To use your own custom icon:

1. **Replace the source**: Create a new `icon_highres.png` (1024×1024 recommended)
2. **Update standard**: Optionally update `icon.png` (64×64)
3. **Rebuild**: Run the build script to generate platform-specific versions

### Creating High-Quality Icons

For professional results:
- Start with vector graphics (SVG, AI, Figma)
- Export at 1024×1024 or higher
- Use PNG with transparency
- Test at multiple sizes (16×16 to 512×512)

## 🔍 File Size Comparison

| Platform | File | Size | Contains |
|----------|------|------|----------|
| Source | `icon_highres.png` | 8.6 KB | 1024×1024 source (root dir) |
| macOS | `build/icon.icns` | 140 KB | 10 sizes (16×16 to 1024×1024) |
| Windows | `build/icon.ico` | 4 KB | 6 sizes (16×16 to 256×256) |
| Linux | `build/icon.png` | 3.4 KB | 64×64 standard |

## 🛠️ Development

### Testing Icon Generation
```bash
# Test the icon generation function
python -c "from build_app import generate_platform_icons; generate_platform_icons()"

# Test GUI with icons
python gui.py
```

### Manual Icon Generation
```bash
# macOS only (requires iconutil)
python build_app.py  # Will generate icons automatically

# Or manually:
mkdir -p build/icon.iconset
# ... create sizes manually in build/icon.iconset/ ...
iconutil -c icns build/icon.iconset -o icon.icns
```

## 🚫 Troubleshooting

### "iconutil not found"
- **Solution**: Install Xcode Command Line Tools on macOS
- **Alternative**: Use PNG fallback (will work but less optimal)

### "PIL not installed"
- **Solution**: `pip install Pillow`
- **Required for**: Windows ICO generation and icon resizing

### "No icon source files"
- **Solution**: Ensure `icon_highres.png` or `icon.png` exists
- **Check**: Run `ls icon*.png` in project root

## 📄 License

The generated icons are simple geometric shapes and can be used freely. See main LICENSE file for application licensing. 