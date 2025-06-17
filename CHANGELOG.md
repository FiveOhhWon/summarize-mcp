# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-17

### Added
- Persistent state management for voice and tone preferences
- `set_voice` tool to set the default voice for all future conversions
- `set_tone` tool to set the default tone/instructions for all future conversions
- Support for new OpenAI voices: ash, ballad, and sage (10 voices total)
- State file saved to `~/.summarize-mcp-state.json`
- Automatic state loading on startup

### Changed
- `play_summary` tool now uses saved voice and tone preferences unless explicitly overridden
- Updated voice list to include all available OpenAI voices
- Tool descriptions updated to reflect persistent preference behavior
- Documentation updated with new tools and usage examples

### Technical Details
- Implemented UserState interface for type-safe state management
- Added loadState() and saveState() functions for persistence
- State validation ensures only valid voices are loaded
- Graceful fallback to defaults if state file is corrupted

## [1.1.1] - 2025-01-17

### Changed
- Updated default instructions to "Keep the summary as short and concise as possible. Speak in a clear and informative tone."
- Tool description now mentions that summaries will be kept short unless otherwise specified
- Documentation updated to reflect the new default behavior

## [1.1.0] - 2025-01-17

### Added
- Cross-platform audio playback support
- Windows support using PowerShell with Windows Media Player
- Linux support with automatic detection of available audio players:
  - mpg123 (recommended)
  - sox (play command)
  - ffmpeg (ffplay command)
  - VLC (cvlc command)
  - ALSA utils (aplay command)
- Fallback audio player that opens files with system default application
- Platform detection logging showing OS type and version
- Audio player interface for extensible playback support

### Changed
- Refactored audio playback into modular player classes
- Updated error messages to be platform-aware
- Enhanced logging to show which audio player is being used
- Documentation updated for multi-platform installation and usage

### Technical Details
- Implemented AudioPlayer interface with check() and play() methods
- Added AfplayPlayer for macOS
- Added WindowsPlayer using PowerShell script
- Added LinuxPlayer with multi-tool support
- Added FallbackPlayer as last resort
- Audio player selection happens automatically on startup

## [1.0.0] - 2025-01-17

### Added
- Initial release
- Core TTS functionality with OpenAI integration
- Support for 7 different voices (alloy, echo, fable, onyx, nova, shimmer, coral)
- Custom speaking instructions
- Background audio playback on macOS using `afplay`
- Automatic file cleanup after playback
- Old file purging on startup (files older than 1 hour)
- TypeScript implementation with full type safety
- Comprehensive error handling with specific error types
- Input validation using Zod schemas
- Debug logging mode
- MCP server implementation following the Model Context Protocol specification

### Technical Details
- Built with TypeScript for type safety
- Uses OpenAI's `gpt-4o-mini-tts` model
- Temporary files stored in system temp directory
- Automatic cleanup after 10 seconds
- Platform check for macOS compatibility
- Validates `afplay` availability on startup

[1.0.0]: https://github.com/FiveOhhWon/summarize-mcp/releases/tag/v1.0.0