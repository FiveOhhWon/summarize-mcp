# summarize-mcp

> 🤖 **Co-authored with [Claude Code](https://claude.ai/referral/uralRLy1tw)** - Making AI summaries audible since 2025! 🔊

A Model Context Protocol (MCP) server that converts text summaries to speech using OpenAI's TTS API and plays them in the background across all major platforms (macOS, Windows, Linux).

## 🌟 Overview

summarize-mcp enables LLMs to convert any text summary into natural-sounding speech using OpenAI's state-of-the-art text-to-speech models. Perfect for creating audio summaries of documents, articles, or any content that benefits from an auditory presentation.

## 🚀 Key Features

- **🎯 Simple & Focused**: One tool that does one thing exceptionally well
- **🎤 Multiple Voices**: Choose from 7 distinct OpenAI voices (alloy, echo, fable, onyx, nova, shimmer, coral)
- **🎨 Custom Instructions**: Control how the text should be spoken
- **🔧 Background Playback**: Audio plays in the background without blocking
- **🌍 Cross-Platform**: Works on macOS, Windows, and Linux
- **💾 Persistent Preferences**: Save your favorite voice and tone settings
- **🎯 Multiple Tools**: Set voice, set tone, and play summaries
- **🧹 Automatic Cleanup**: Temporary files are cleaned up automatically
- **🛡️ Type-Safe**: Full TypeScript support with Zod validation
- **📊 Comprehensive Logging**: Debug mode for troubleshooting
- **⚡ Performance Optimized**: Efficient file handling and cleanup

## 📋 Prerequisites

- **Node.js** 16 or higher
- **OpenAI API Key** with access to TTS models
- **Audio Player** (automatically detected):
  - **macOS**: Built-in `afplay` (no installation needed)
  - **Windows**: Built-in Windows Media Player (no installation needed)
  - **Linux**: One of: `mpg123`, `sox` (`play`), `ffmpeg` (`ffplay`), `vlc` (`cvlc`), or `alsa-utils` (`aplay`)

## 📦 Installation

### Using npx (recommended)

```bash
npx @fiveohhwon/summarize-mcp
```

### From npm

```bash
npm install -g @fiveohhwon/summarize-mcp
```

### From Source

```bash
git clone https://github.com/FiveOhhWon/summarize-mcp.git
cd summarize-mcp
npm install
npm run build
```

## 🏃 Configuration

### Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Using npx (recommended):

```json
{
  "mcpServers": {
    "summarize": {
      "command": "npx",
      "args": ["-y", "@fiveohhwon/summarize-mcp"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

#### Using global install:

```json
{
  "mcpServers": {
    "summarize": {
      "command": "summarize-mcp",
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

#### Using local build:

```json
{
  "mcpServers": {
    "summarize": {
      "command": "node",
      "args": ["/absolute/path/to/summarize-mcp/dist/index.js"],
      "env": {
        "OPENAI_API_KEY": "your-openai-api-key"
      }
    }
  }
}
```

### Environment Variables

- **`OPENAI_API_KEY`** (required): Your OpenAI API key
- **`DEBUG`** (optional): Set to `"true"` for verbose logging

## 🛠️ Available Tools

### play_summary

Converts text to speech and plays it in the background. Uses saved voice and tone preferences unless overridden.

**Parameters:**
- `summary` (required): The text to convert to speech
- `voice` (optional): Voice to use - `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, or `shimmer` (uses saved preference if not specified)
- `instructions` (optional): Instructions for how the text should be spoken (uses saved tone if not specified)

**Example:**
```json
{
  "summary": "The quick brown fox jumps over the lazy dog. This pangram contains all letters of the alphabet.",
  "voice": "nova",
  "instructions": "Speak slowly and clearly, emphasizing each word."
}
```

### set_voice

Set the default voice for all future text-to-speech conversions.

**Parameters:**
- `voice` (required): The voice to use - `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, or `shimmer`

**Example:**
```json
{
  "voice": "nova"
}
```

### set_tone

Set the default tone/instructions for how text should be spoken in all future TTS requests.

**Parameters:**
- `tone` (required): The tone/instructions to use (e.g., "Speak slowly and calmly", "Be enthusiastic and energetic")

**Example:**
```json
{
  "tone": "Speak in a warm, friendly manner with moderate pacing"
}
```

## 📖 Usage Examples

### Basic Summary

```
"Please summarize this article and play it as audio"
```

The LLM will:
1. Generate a summary of the content
2. Use the `play_summary` tool to convert it to speech
3. The audio will play in the background with saved preferences

### Set Default Voice

```
"Set the default voice to nova"
```

This will save "nova" as your preferred voice for all future summaries.

### Set Default Tone

```
"Set the tone to be warm and conversational with a slower pace"
```

This will save your tone preference for all future summaries.

### Custom Voice (One-time)

```
"Summarize this document and play it using the 'sage' voice"
```

This will use "sage" for this summary only, without changing your default.

### With Custom Instructions (One-time)

```
"Create an audio summary of this text. Make it sound enthusiastic and energetic."
```

This will use custom instructions for this summary only.

## 🎯 Voice Options

| Voice | Description |
|-------|-------------|
| `alloy` | Neutral and balanced |
| `ash` | Warm and engaging |
| `ballad` | Expressive and dramatic |
| `coral` | Clear and professional (default) |
| `echo` | Smooth and reflective |
| `fable` | Expressive and animated |
| `nova` | Friendly and upbeat |
| `onyx` | Deep and authoritative |
| `sage` | Wise and measured |
| `shimmer` | Soft and gentle |

## 🧪 Development

```bash
# Install dependencies
npm install

# Run in development mode with hot reload
npm run dev

# Build for production
npm run build

# Type checking
npm run typecheck

# Run with debug logging
DEBUG=true npm run dev
```

## 🏗️ Architecture

```
summarize-mcp/
├── src/
│   └── index.ts        # Main MCP server implementation
├── dist/               # Compiled JavaScript (generated)
├── package.json        # Project metadata and scripts
├── tsconfig.json       # TypeScript configuration
└── README.md          # This file
```

## 🔧 Technical Details

- **Audio Format**: MP3 (OpenAI TTS output format)
- **Temporary Files**: Stored in system temp directory
- **File Cleanup**: Automatic cleanup after 10 seconds (configurable)
- **Old File Purge**: Files older than 1 hour are cleaned on startup
- **Platform Support**:
  - **macOS**: Uses built-in `afplay`
  - **Windows**: Uses PowerShell with Windows Media Player
  - **Linux**: Auto-detects available player (mpg123, sox, ffmpeg, vlc, alsa)
  - **Fallback**: Opens with system default audio application
- **State Management**: 
  - Preferences saved to `~/.summarize-mcp-state.json`
  - Persists voice and tone settings between sessions
  - Automatic loading on startup
- **Error Handling**: Comprehensive error handling with specific error types
- **Validation**: Input validation using Zod schemas

## 🚨 Troubleshooting

### "OPENAI_API_KEY environment variable is not set"
Set your OpenAI API key in the Claude Desktop configuration.

### "No audio player available"
**Linux users**: Install one of the supported audio players:
```bash
# Ubuntu/Debian
sudo apt-get install mpg123
# or
sudo apt-get install sox
# or
sudo apt-get install ffmpeg
# or
sudo apt-get install vlc

# Fedora/RHEL
sudo dnf install mpg123
# or similar for other players

# Arch
sudo pacman -S mpg123
# or similar for other players
```

**Windows/macOS**: Audio playback should work out of the box.

### Audio doesn't play
1. Check system volume
2. Ensure no other audio issues on your system
3. Enable debug logging with `DEBUG=true`
4. Check the logs for any errors

## 📝 Changelog

### v1.2.0 (Persistent Preferences)
- 💾 Added persistent state management for voice and tone preferences
- 🎯 Added `set_voice` tool to set default voice
- 🎯 Added `set_tone` tool to set default speaking instructions
- 🎆 Added support for new OpenAI voices: ash, ballad, and sage
- 🔄 `play_summary` now uses saved preferences unless overridden
- 📝 State saved to `~/.summarize-mcp-state.json`

### v1.1.0 (Cross-Platform Support)
- 🌍 Added Windows support using PowerShell/Windows Media Player
- 🐧 Added Linux support with auto-detection of audio players
- 🔄 Added fallback to system default audio player
- 📝 Updated documentation for multi-platform usage

### v1.0.0 (Initial Release)
- 🎉 Initial release
- ✨ Core TTS functionality with OpenAI integration
- ✨ Support for 7 different voices
- ✨ Custom speaking instructions
- ✨ Background audio playback on macOS
- ✨ Automatic file cleanup
- ✨ TypeScript implementation
- ✨ Comprehensive error handling

## 🔮 Roadmap

- [x] Cross-platform audio playback (Windows, Linux)
- [ ] Additional TTS providers (ElevenLabs, Amazon Polly)
- [ ] Audio format options (WAV, OGG)
- [ ] Playback control (pause, resume, stop)
- [ ] Queue management for multiple summaries
- [ ] Audio file caching
- [ ] Speed and pitch controls
- [ ] SSML support for advanced speech control

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://github.com/anthropics/model-context-protocol) specification by Anthropic
- Powered by [OpenAI's TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- Special thanks to the MCP community for inspiration and support