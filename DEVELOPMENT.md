# Development Guide

This guide covers how to set up the development environment, run the applications, and build standalone executables.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running the Applications](#running-the-applications)
- [Building Executables](#building-executables)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.7+** (recommended: 3.9 or higher)
- **Git** for version control
- **Homebrew** (macOS) or appropriate package manager for your OS

### Platform-Specific Requirements

#### macOS
```bash
# Install Python with tkinter support
brew install python-tk

# Verify tkinter is available
python3 -c "import tkinter; print('✅ tkinter available')"
```

#### Windows
```bash
# Python from python.org includes tkinter by default
# Or use Windows Store Python
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install python3-tk python3-dev
```

## Development Setup

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd timecodes
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies (for building executables)
pip install -r requirements-dev.txt

# Or install everything at once
pip install -e .[dev]
```

### 4. Verify Installation

```bash
# Test core functionality
python -c "import core, config; print('✅ Core modules work')"

# Test GUI (requires tkinter)
python -c "import gui; print('✅ GUI module works')"

# Test CLI
python video_chapters.py --help
```

## Project Structure

```
timecodes/
├── core.py              # Core processing logic
├── config.py            # Configuration and settings management
├── gui.py              # GUI application (tkinter)
├── video_chapters.py   # CLI application
├── build_app.py        # Build script for executables
├── setup.py            # Python package setup
├── requirements.txt     # Runtime dependencies
├── requirements-dev.txt # Development dependencies
├── README.md           # User documentation
├── DEVELOPMENT.md      # This file
├── LICENSE             # Apache 2.0 license
├── .gitignore          # Git ignore patterns
└── venv/               # Virtual environment (ignored)
```

### Module Overview

- **`core.py`**: Contains `YouTubeProcessor` class and core functionality
- **`config.py`**: Handles secure settings storage and configuration management
- **`gui.py`**: Modern tkinter GUI with tabbed interface and real-time progress
- **`video_chapters.py`**: Command-line interface using the core module
- **`build_app.py`**: Automated build script for creating executables

## Running the Applications

### GUI Application

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Run GUI
python gui.py
```

**GUI Features:**
- YouTube URL input with language checking
- Secure API key management (Save/Clear buttons)
- Language selection dropdown
- Model selection (Gemini Pro/Flash)
- Processing options (checkboxes)
- Tabbed results (Progress, Subtitles, Chapters)
- Save functionality for results

### CLI Application

```bash
# Activate virtual environment
source venv/bin/activate

# Basic usage
python video_chapters.py "https://youtube.com/watch?v=VIDEO_ID" --api-key YOUR_KEY

# Check available languages
python video_chapters.py --check-languages "https://youtube.com/watch?v=VIDEO_ID"

# With specific options
python video_chapters.py \
  --language en \
  --model gemini-2.5-flash \
  --keep-files \
  --quiet \
  "https://youtube.com/watch?v=VIDEO_ID"
```

## Building Executables

### Quick Build (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Build both GUI and CLI applications
python build_app.py

# Build GUI only
python build_app.py --gui-only

# Build CLI only
python build_app.py --cli-only

# Build without cleanup (keep build files)
python build_app.py --no-clean
```

### Production Build with Code Signing

#### macOS Code Signing and Notarization

```bash
# Build with code signing (using partial name)
python build_app.py --sign --signing-identity "Your Name"

# Build with code signing and DMG creation
python build_app.py --sign --signing-identity "Your Name" --create-dmg

# Build with full notarization
python build_app.py \
  --sign \
  --signing-identity "Your Name" \
  --create-dmg \
  --notary-profile your-notary-profile
```

#### Windows Code Signing

```bash
# Build with code signing
python build_app.py --sign --cert-path "path/to/certificate.p12" --cert-password "your_password"

# Build with custom timestamp server
python build_app.py \
  --sign \
  --cert-path "path/to/certificate.p12" \
  --cert-password "your_password" \
  --timestamp-url "http://timestamp.digicert.com"
```

### Manual PyInstaller Build

#### GUI Application

```bash
# macOS
pyinstaller --onefile --windowed --name "YouTube Chapters" gui.py

# Windows
pyinstaller --onefile --windowed --name "YouTube Chapters" gui.py

# Linux
pyinstaller --onefile --windowed --name "YouTube Chapters" gui.py
```

#### CLI Application

```bash
# All platforms
pyinstaller --onefile --name "youtube-chapters-cli" video_chapters.py
```

### Build Output

After building, executables will be in the `dist/` directory:

```
dist/
├── YouTube Chapters      # GUI app (macOS/Linux)
├── YouTube Chapters.exe  # GUI app (Windows)
├── YouTube Chapters.dmg  # Signed DMG (macOS, if --create-dmg used)
├── youtube-chapters-cli  # CLI app (macOS/Linux)
└── youtube-chapters-cli.exe  # CLI app (Windows)
```

## Code Signing Setup

Code signing is essential for distributing applications to end users, as it provides security verification and prevents security warnings.

### macOS Code Signing Setup

#### Prerequisites

1. **Apple Developer Account** (required for distribution)
2. **Xcode Command Line Tools**
3. **Developer ID Certificate** in Keychain

#### 1. Install Xcode Command Line Tools

```bash
xcode-select --install
```

#### 2. Get Developer ID Certificate

1. Go to [Apple Developer Portal](https://developer.apple.com/account/resources/certificates)
2. Create a "Developer ID Application" certificate
3. Download and install in Keychain Access
4. Find your signing identity:

```bash
# List available signing identities
security find-identity -v -p codesigning

# Example output:
# 1) 1234567890ABCDEF "Developer ID Application: Your Name (TEAM_ID)"
```

#### 3. Setup Notarization (Optional but Recommended)

1. Create an App Store Connect API key:
   - Go to [App Store Connect](https://appstoreconnect.apple.com/access/api)
   - Create a new API key with "Developer" role
   - Download the `.p8` file

2. Setup keychain profile:

```bash
# Store credentials in keychain
xcrun notarytool store-credentials your-notary-profile \
  --apple-id "your-email@example.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "app-specific-password"

# Or using API key:
xcrun notarytool store-credentials your-notary-profile \
  --key "path/to/AuthKey_KEYID.p8" \
  --key-id "KEY_ID" \
  --issuer "ISSUER_ID"
```

#### 4. Verify Setup

```bash
# Test signing
codesign --sign "Developer ID Application: Your Name (TEAM_ID)" --verify --verbose test_file

# Test notarization credentials
xcrun notarytool history --keychain-profile your-notary-profile
```

### Windows Code Signing Setup

#### Prerequisites

1. **Code Signing Certificate** (from trusted CA like DigiCert, Sectigo, etc.)
2. **Windows SDK** (for signtool.exe)

#### 1. Install Windows SDK

Download and install [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) which includes `signtool.exe`.

#### 2. Get Code Signing Certificate

**Option A: File-based Certificate (.p12/.pfx)**
- Purchase from a trusted CA (DigiCert, Sectigo, etc.)
- Download as `.p12` or `.pfx` file
- Keep the password secure

**Option B: Hardware Security Module (HSM)**
- For higher security (required for EV certificates)
- Certificate stored on USB token or cloud HSM

#### 3. Verify signtool.exe

```bash
# Check if signtool is available
signtool.exe /?

# If not found, add Windows SDK to PATH:
# C:\Program Files (x86)\Windows Kits\10\bin\10.0.XXXXX.X\x64\
```

#### 4. Test Signing

```bash
# Test with your certificate
signtool.exe sign /f "path\to\certificate.p12" /p "password" /t "http://timestamp.sectigo.com" /v "test_file.exe"
```

### Build Script Options

#### Command Line Arguments

```bash
python build_app.py --help
```

**Build Options:**
- `--gui-only`: Build GUI application only
- `--cli-only`: Build CLI application only  
- `--no-clean`: Don't clean up build files

**Signing Options:**
- `--sign`: Enable code signing
- `--signing-identity`: macOS code signing identity (can be partial name like "Your Name" or full identity)
- `--notary-profile`: macOS notarization keychain profile
- `--create-dmg`: Create DMG package (macOS)
- `--cert-path`: Windows certificate file path
- `--cert-password`: Windows certificate password
- `--timestamp-url`: Timestamp server URL

#### Example Production Builds

```bash
# macOS: Full signed and notarized build
python build_app.py \
  --sign \
  --signing-identity "Your Name" \
  --create-dmg \
  --notary-profile your-notary-profile

# Windows: Signed build
python build_app.py \
  --sign \
  --cert-path "certificates/code-signing.p12" \
  --cert-password "your_secure_password"

# Cross-platform: GUI only with signing
python build_app.py \
  --gui-only \
  --sign \
  --signing-identity "Your Name" \
  --cert-path "certificates/code-signing.p12"
```

## Development Workflow

### 1. Making Changes

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make your changes
# Edit files...

# Test changes
python gui.py  # Test GUI
python video_chapters.py --help  # Test CLI
```

### 2. Testing

```bash
# Test imports
python -c "import core, config, gui; print('All imports successful')"

# Test with real YouTube URL (requires API key)
export GEMINI_API_KEY="your-key-here"
python video_chapters.py --check-languages "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

### 3. Building and Testing Executables

```bash
# Build executables
python build_app.py

# Test built executables
./dist/YouTube\ Chapters  # Test GUI (macOS/Linux)
./dist/youtube-chapters-cli --help  # Test CLI
```

### 4. Committing Changes

```bash
# Add files
git add .

# Commit with descriptive message
git commit -m "Add new feature: description of changes"

# Push to remote
git push origin feature/new-feature
```

## Testing

### Unit Testing

```bash
# Run basic import tests
python -c "
import core
import config
import gui
print('✅ All modules import successfully')
"
```

### Integration Testing

```bash
# Test YouTube processor (requires internet)
python -c "
from core import YouTubeProcessor
processor = YouTubeProcessor()
langs = processor.get_available_languages('https://youtube.com/watch?v=dQw4w9WgXcQ')
print(f'✅ Found languages: {list(langs.keys())}')
"
```

### GUI Testing

```bash
# Test GUI startup (will open window briefly)
timeout 3 python gui.py || echo "✅ GUI started successfully"
```

## Troubleshooting

### Common Issues

#### 1. tkinter Not Available

**Error**: `ModuleNotFoundError: No module named '_tkinter'`

**Solution**:
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk

# Windows
# Reinstall Python from python.org (includes tkinter)
```

#### 2. PyInstaller Build Fails

**Error**: Various PyInstaller errors

**Solution**:
```bash
# Clean previous builds
rm -rf build/ dist/ *.spec

# Update PyInstaller
pip install --upgrade pyinstaller

# Try with verbose output
pyinstaller --onefile --windowed --debug all gui.py
```

#### 3. API Key Issues

**Error**: `No module named 'keyring'` or keyring failures

**Solution**:
```bash
# Reinstall keyring
pip uninstall keyring
pip install keyring

# On Linux, install secret service
sudo apt-get install python3-secretstorage
```

#### 4. Import Errors

**Error**: `ModuleNotFoundError` for custom modules

**Solution**:
```bash
# Ensure you're in the correct directory
pwd  # Should show .../timecodes

# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall in development mode
pip install -e .
```

#### 5. Code Signing Issues (macOS)

**Error**: `codesign: command not found`

**Solution**:
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

**Error**: `no identity found`

**Solution**:
```bash
# List available identities
security find-identity -v -p codesigning

# If empty, create and install Developer ID certificate from Apple Developer Portal
```

**Error**: `notarytool: command not found`

**Solution**:
```bash
# Update Xcode Command Line Tools
sudo xcode-select --reset
xcode-select --install
```

**Error**: Notarization fails with authentication error

**Solution**:
```bash
# Verify keychain profile
xcrun notarytool history --keychain-profile your-notary-profile

# If fails, recreate profile:
xcrun notarytool store-credentials your-notary-profile \
  --apple-id "your-email@example.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "app-specific-password"
```

#### 6. Code Signing Issues (Windows)

**Error**: `signtool.exe: command not found`

**Solution**:
```bash
# Install Windows SDK and add to PATH
# Or use full path:
"C:\Program Files (x86)\Windows Kits\10\bin\10.0.XXXXX.X\x64\signtool.exe"
```

**Error**: Certificate password prompt

**Solution**:
```bash
# Use environment variable for password (more secure)
set CERT_PASSWORD=your_password
python build_app.py --sign --cert-path "cert.p12" --cert-password "%CERT_PASSWORD%"
```

**Error**: `The specified timestamp server either could not be reached`

**Solution**:
```bash
# Try different timestamp servers:
python build_app.py --sign --timestamp-url "http://timestamp.digicert.com"
python build_app.py --sign --timestamp-url "http://timestamp.sectigo.com"
python build_app.py --sign --timestamp-url "http://timestamp.globalsign.com/tsa/r6advanced1"
```

### Debug Mode

#### Enable Verbose Logging

```python
# Add to any .py file for debugging
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### PyInstaller Debug

```bash
# Build with debug information
pyinstaller --onefile --windowed --debug all --log-level DEBUG gui.py
```

## Package Management

### Adding New Dependencies

1. **Runtime dependency** (needed to run the app):
   ```bash
   # Add to requirements.txt
   echo "new-package>=1.0.0" >> requirements.txt
   pip install new-package
   ```

2. **Development dependency** (only for building):
   ```bash
   # Add to requirements-dev.txt
   echo "dev-package>=1.0.0" >> requirements-dev.txt
   pip install dev-package
   ```

3. **Update setup.py** if adding new dependencies

### Version Management

```bash
# Check current versions
pip list

# Generate current requirements
pip freeze > requirements-current.txt

# Update all packages
pip install --upgrade -r requirements.txt -r requirements-dev.txt
```

## Release Process

### 1. Prepare Release

```bash
# Update version in setup.py
# Update CHANGELOG.md if you have one
# Test everything works

# Build and test executables (unsigned for testing)
python build_app.py
# Test the built executables

# Build production signed executables
# macOS:
python build_app.py \
  --sign \
  --signing-identity "Your Name" \
  --create-dmg \
  --notary-profile your-notary-profile

# Windows:
python build_app.py \
  --sign \
  --cert-path "path/to/certificate.p12" \
  --cert-password "your_password"
```

### 2. Create Release

```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push with tags
git push origin main --tags
```

### 3. Distribute

- Upload executables from `dist/` folder
- Or publish to PyPI: `python setup.py sdist bdist_wheel && twine upload dist/*`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (GUI, CLI, builds)
5. Update documentation if needed
6. Submit a pull request

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Google Gemini AI Documentation](https://ai.google.dev/docs)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp) 