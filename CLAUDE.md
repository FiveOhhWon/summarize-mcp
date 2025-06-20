# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Running the Server
- `python -m summarize_mcp` - Run the MCP server
- `python test.py` - Run the test script
- `pip install -r requirements.txt` - Install dependencies
- `pip install -e .` - Install in development mode

### Before Publishing
- Test the server with `python test.py`
- Ensure all dependencies are listed in `requirements.txt` and `pyproject.toml`

## Architecture Overview

This is a Model Context Protocol (MCP) server that provides text-to-speech functionality using OpenAI's TTS API. The architecture consists of:

1. **MCP Server Implementation** (`src/summarize_mcp/server.py`):
   - Uses stdio transport for communication with MCP clients
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
   - Uses Pydantic for runtime validation of all inputs
   - Preferences override defaults unless explicitly specified in tool calls

## Key Implementation Details

- Written in Python 3.8+ with async/await support
- Uses Pydantic for data validation (Python equivalent of Zod)
- Environment variable `OPENAI_API_KEY` is required
- Debug logging available via `DEBUG=true` environment variable
- Can be run directly with `python -m summarize_mcp` or installed as a package