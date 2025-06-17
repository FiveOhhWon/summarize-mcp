# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Build and Development
- `npm run build` - Compile TypeScript to JavaScript in the dist/ directory
- `npm run dev` - Run in development mode with hot reload using tsx
- `npm run typecheck` - Type check without emitting files
- `npm run test` - Build and run test.js file

### Before Publishing
- Always run `npm run typecheck` to ensure type safety
- The `prepublishOnly` script automatically runs the build

## Architecture Overview

This is a Model Context Protocol (MCP) server that provides text-to-speech functionality using OpenAI's TTS API. The architecture consists of:

1. **MCP Server Implementation** (`src/index.ts`):
   - Uses StdioServerTransport for communication with MCP clients
   - Implements three tools: `play_summary`, `set_voice`, and `set_tone`
   - Manages persistent user preferences in `~/.summarize-mcp-state.json`

2. **Cross-Platform Audio Playback**:
   - macOS: Uses built-in `afplay`
   - Windows: Uses PowerShell with Windows Media Player
   - Linux: Auto-detects available players (mpg123, sox, ffmpeg, vlc, alsa)
   - Fallback: Opens with system default audio application

3. **File Management**:
   - Creates temporary MP3 files in system temp directory
   - Automatic cleanup after 10 seconds
   - Purges files older than 1 hour on startup

4. **State Management**:
   - Persists user voice and tone preferences between sessions
   - Uses Zod for runtime validation of all inputs
   - Preferences override defaults unless explicitly specified in tool calls

## Key Implementation Details

- The server is designed as an ES module (type: "module" in package.json)
- Strict TypeScript configuration with all strict checks enabled
- Environment variable `OPENAI_API_KEY` is required
- Debug logging available via `DEBUG=true` environment variable
- The entry point includes a shebang for direct execution when installed globally