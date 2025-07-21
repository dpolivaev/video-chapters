# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enhanced error debugging with yt-dlp debug output capture and display
- Improved GUI responsiveness during error handling

### Fixed
- Windows build and icon issues
- Menu commands for instructions tab
- Build process improvements

## [1.1.1] - 2025-01-XX

### Added
- Windows app distribution as zipped directory
- Refactored instruction history into separate module with `InstructionHistoryDialog` class

### Changed
- Renamed start button for better clarity
- Updated GitHub URL references

### Fixed
- Build process issues
- Various build output improvements

## [1.1.0] - 2025-01-XX

### Added
- **Custom Instructions Feature**: Users can now add custom instructions for AI processing
- **Instruction History**: Save and reuse previously applied user instructions
- Enhanced UI feedback and user experience improvements

### Changed
- Improved GUI layout and functionality
- Better settings management (save all settings only at the end)
- Enhanced build output and process

### Fixed
- Import issues
- Menu commands and widget focus handling
- Various GUI improvements

## [1.0.1] - 2025-01-XX

### Added
- Custom icon support for Windows applications
- Edit menu with standard operations (cut, copy, paste, select all)
- Error handling for API key updates
- Microsoft redistributable hint for Windows users

### Changed
- Improved API key handling and security
- Enhanced build process

### Fixed
- Various build improvements
- README documentation updates

## [1.0.0] - 2025-01-XX

### Added
- **GUI Application**: Complete graphical user interface for video processing
- **Cross-platform Support**: Windows, macOS, and Linux compatibility
- **Code Signing and Notarization**: macOS app signing and notarization support
- **Icon System**: Cross-platform icon system with build-time generation
- **About Dialog**: Application information and license display
- **License Integration**: Apache 2.0 license integration

### Changed
- Refactored codebase to support GUI and CLI modes
- Improved interactive mode functionality
- Enhanced language selection capabilities
- Better prompt engineering for AI processing

### Fixed
- macOS DMG creation
- Windows executable creation as single file
- License file location for Windows builds
- Various build and GUI improvements

### Technical
- Comprehensive development guide
- Enhanced .gitignore configuration
- Improved build scripts and automation
- Code signing and notarization workflows

---

## Version History Notes

- **v1.0.0**: Initial stable release with GUI and cross-platform support
- **v1.0.1**: Bug fixes and Windows-specific improvements
- **v1.1.0**: Major feature addition with custom instructions and history
- **v1.1.1**: Build improvements and code refactoring
- **Unreleased**: Enhanced error debugging and GUI responsiveness 