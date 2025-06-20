#!/usr/bin/env python3
"""MCP server for text-to-speech summaries using OpenAI's TTS API."""

import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from mcp.server import FastMCP
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    "temp_dir": Path(tempfile.gettempdir()) / "summarize-mcp",
    "cleanup_delay": 10,  # seconds
    "default_voice": "coral",
    "default_instructions": "Keep the summary as short and concise as possible. Speak in a clear and informative tone.",
    "state_file": Path.home() / ".summarize-mcp-state.json",
}

# Valid voices from OpenAI
VALID_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "true" else logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Pydantic models for validation
class PlaySummaryArgs(BaseModel):
    summary: str = Field(..., min_length=1, description="The text summary to convert to speech and play")
    voice: Optional[str] = Field(None, description="The voice to use for TTS (optional, uses saved preference if not specified)")
    instructions: Optional[str] = Field(None, description="Instructions for how the text should be spoken (optional, uses saved tone if not specified)")
    
    @field_validator("voice")
    def validate_voice(cls, v):
        if v is not None and v not in VALID_VOICES:
            raise ValueError(f"Voice must be one of: {', '.join(VALID_VOICES)}")
        return v


class SetVoiceArgs(BaseModel):
    voice: str = Field(..., description="The voice to use for all future TTS requests")
    
    @field_validator("voice")
    def validate_voice(cls, v):
        if v not in VALID_VOICES:
            raise ValueError(f"Voice must be one of: {', '.join(VALID_VOICES)}")
        return v


class SetToneArgs(BaseModel):
    tone: str = Field(..., min_length=1, description="The tone/instructions to use for all future TTS requests")


class UserState(BaseModel):
    voice: str = CONFIG["default_voice"]
    tone: str = CONFIG["default_instructions"]


# Custom error class
class TTSError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


# State management
current_state = UserState()


async def load_state() -> None:
    """Load saved state from file."""
    global current_state
    try:
        if CONFIG["state_file"].exists():
            with open(CONFIG["state_file"], "r") as f:
                data = json.load(f)
                current_state = UserState(**data)
                logger.debug(f"Loaded state: {current_state}")
    except Exception as e:
        logger.debug(f"No state file found or invalid, using defaults: {e}")
        current_state = UserState()


async def save_state() -> None:
    """Save current state to file."""
    try:
        with open(CONFIG["state_file"], "w") as f:
            json.dump(current_state.model_dump(), f, indent=2)
        logger.debug(f"Saved state: {current_state}")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


# Audio player classes
class AudioPlayer:
    """Base class for audio players."""
    name = "Base Audio Player"
    
    async def check(self) -> bool:
        """Check if this player is available."""
        return False
    
    async def play(self, file_path: str) -> None:
        """Play the audio file."""
        raise NotImplementedError


class AfplayPlayer(AudioPlayer):
    """macOS audio player using afplay."""
    name = "afplay (macOS)"
    
    async def check(self) -> bool:
        if platform.system() != "Darwin":
            return False
        return shutil.which("afplay") is not None
    
    async def play(self, file_path: str) -> None:
        subprocess.Popen(
            ["afplay", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


class WindowsPlayer(AudioPlayer):
    """Windows audio player using PowerShell."""
    name = "Windows Media Player"
    
    async def check(self) -> bool:
        return platform.system() == "Windows"
    
    async def play(self, file_path: str) -> None:
        script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $player = New-Object System.Media.SoundPlayer
        $player.SoundLocation = '{file_path.replace("'", "''")}'
        $player.Play()
        """
        subprocess.Popen(
            ["powershell", "-Command", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )


class LinuxPlayer(AudioPlayer):
    """Linux audio player using various tools."""
    name = "Linux audio player"
    command: Optional[str] = None
    
    async def check(self) -> bool:
        if platform.system() != "Linux":
            return False
        
        # Check for available audio players in order of preference
        players = ["mpg123", "play", "aplay", "ffplay", "cvlc"]
        
        for player in players:
            if shutil.which(player):
                self.command = player
                logger.debug(f"Found Linux audio player: {player}")
                return True
        
        return False
    
    async def play(self, file_path: str) -> None:
        if not self.command:
            raise RuntimeError("No audio player available")
        
        args = [file_path]
        
        # Add specific arguments for different players
        if self.command == "cvlc":
            args = ["--play-and-exit", "--intf", "dummy", file_path]
        elif self.command == "ffplay":
            args = ["-nodisp", "-autoexit", file_path]
        
        subprocess.Popen(
            [self.command] + args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


class FallbackPlayer(AudioPlayer):
    """Fallback player using system default."""
    name = "Fallback (open with default app)"
    
    async def check(self) -> bool:
        return True  # Always available as last resort
    
    async def play(self, file_path: str) -> None:
        if platform.system() == "Darwin":
            cmd = "open"
        elif platform.system() == "Windows":
            cmd = "start"
        else:
            cmd = "xdg-open"
        
        subprocess.Popen(
            [cmd, file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=(platform.system() == "Windows")
        )


async def get_audio_player() -> Optional[AudioPlayer]:
    """Get the appropriate audio player for the current platform."""
    players = [
        AfplayPlayer(),
        WindowsPlayer(),
        LinuxPlayer(),
        FallbackPlayer(),
    ]
    
    for player in players:
        if await player.check():
            logger.info(f"Using audio player: {player.name}")
            return player
    
    return None


async def ensure_temp_dir() -> None:
    """Ensure the temp directory exists."""
    try:
        CONFIG["temp_dir"].mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create temp directory: {e}")
        raise TTSError("Failed to create temporary directory", "TEMP_DIR_ERROR")


async def cleanup_old_files() -> None:
    """Clean up old audio files."""
    try:
        if not CONFIG["temp_dir"].exists():
            return
        
        now = time.time()
        
        for file in CONFIG["temp_dir"].glob("speech_*.mp3"):
            try:
                # Remove files older than 1 hour
                if now - file.stat().st_mtime > 3600:
                    file.unlink()
                    logger.debug(f"Cleaned up old file: {file.name}")
            except Exception:
                # File might be in use, ignore
                pass
    except Exception as e:
        logger.debug(f"Cleanup error (non-critical): {e}")


# Create FastMCP app
mcp = FastMCP("summarize-mcp")


@mcp.tool(
    description="**IMPORTANT TO KEEP THE SUMMARY AS SHORT AND CONCISE AS POSSIBLE** Convert text summary to speech using OpenAI TTS and play it in the background. Keeps summaries under 100 words unless otherwise requested. Uses the saved voice and tone preferences unless overridden."
)
async def play_summary(
    summary: str = Field(..., description="The text summary to convert to speech and play"),
    voice: Optional[str] = Field(None, description="The voice to use for TTS (optional, uses saved preference if not specified)"),
    instructions: Optional[str] = Field(None, description="Instructions for how the text should be spoken (optional, uses saved tone if not specified)")
) -> str:
    """Convert text to speech and play it."""
    global current_state, openai_client, audio_player
    
    try:
        # Validate arguments
        args = PlaySummaryArgs(summary=summary, voice=voice, instructions=instructions)
        
        # Use provided values or fall back to saved state
        voice = args.voice or current_state.voice
        instructions = args.instructions or current_state.tone
        
        logger.info(f"Generating TTS for summary ({len(args.summary)} chars) with voice: {voice}")
        
        # Generate unique filename with timestamp
        timestamp = int(time.time() * 1000)
        speech_file = CONFIG["temp_dir"] / f"speech_{timestamp}.mp3"
        
        # Create TTS audio
        response = openai_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=args.summary,
            instructions=instructions,
        )
        
        # Save to file
        response.stream_to_file(str(speech_file))
        
        logger.info(f"Audio file created: {speech_file}")
        
        # Play the audio in the background
        await audio_player.play(str(speech_file))
        logger.debug(f"Audio playback started with {audio_player.name}")
        
        # Schedule cleanup
        async def cleanup():
            await asyncio.sleep(CONFIG["cleanup_delay"])
            try:
                speech_file.unlink()
                logger.debug(f"Cleaned up audio file: {speech_file}")
            except Exception:
                logger.debug(f"Could not clean up file (might still be playing): {speech_file}")
        
        asyncio.create_task(cleanup())
        
        return f"✅ Summary converted to speech and playing in the background\nVoice: {voice}\nLength: {len(args.summary)} characters"
    
    except Exception as e:
        logger.error(f"Error in play_summary: {e}")
        
        if hasattr(e, "errors"):  # Pydantic validation error
            errors = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"{loc}: {msg}")
            return f"❌ Invalid arguments: {', '.join(errors)}"
        elif isinstance(e, TTSError):
            return f"❌ TTS Error ({e.code}): {str(e)}"
        else:
            return f"❌ Error playing summary: {str(e)}"


@mcp.tool(
    description="Set the default voice for all future text-to-speech conversions. Choose from: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, or shimmer."
)
async def set_voice(
    voice: str = Field(..., description="The voice to use for all future TTS requests")
) -> str:
    """Set the default voice."""
    global current_state
    
    try:
        # Validate arguments
        args = SetVoiceArgs(voice=voice)
        
        # Update state
        current_state.voice = args.voice
        await save_state()
        
        logger.info(f"Default voice changed to: {args.voice}")
        
        return f"✅ Default voice set to: {args.voice}\n\nAll future audio summaries will use this voice unless specifically overridden."
    
    except Exception as e:
        logger.error(f"Error in set_voice: {e}")
        
        if hasattr(e, "errors"):  # Pydantic validation error
            errors = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"{loc}: {msg}")
            return f"❌ Invalid arguments: {', '.join(errors)}"
        else:
            return f"❌ Error setting voice: {str(e)}"


@mcp.tool(
    description="Set the default tone/instructions for how text should be spoken in all future TTS requests."
)
async def set_tone(
    tone: str = Field(..., description="The tone/instructions to use for all future TTS requests (e.g., 'Speak slowly and calmly', 'Be enthusiastic and energetic')")
) -> str:
    """Set the default tone/instructions."""
    global current_state
    
    try:
        # Validate arguments
        args = SetToneArgs(tone=tone)
        
        # Update state
        current_state.tone = args.tone
        await save_state()
        
        logger.info("Default tone changed")
        
        return f'✅ Default tone set to: "{args.tone}"\n\nAll future audio summaries will use this tone unless specifically overridden.'
    
    except Exception as e:
        logger.error(f"Error in set_tone: {e}")
        
        if hasattr(e, "errors"):  # Pydantic validation error
            errors = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"{loc}: {msg}")
            return f"❌ Invalid arguments: {', '.join(errors)}"
        else:
            return f"❌ Error setting tone: {str(e)}"


# Initialize globals at module level
openai_client: Optional[OpenAI] = None
audio_player: Optional[AudioPlayer] = None


async def initialize_server():
    """Initialize the server."""
    global openai_client, audio_player
    
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable is not set")
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    
    openai_client = OpenAI(api_key=api_key)
    
    # Get appropriate audio player for the platform
    audio_player = await get_audio_player()
    if not audio_player:
        logger.error("No audio player found for current platform")
        raise RuntimeError("No audio player available. Please install an audio player (mpg123, sox, ffmpeg, or vlc on Linux)")
    
    # Ensure temp directory exists
    await ensure_temp_dir()
    
    # Clean up old files on startup
    await cleanup_old_files()
    
    # Load saved state
    await load_state()
    
    # Log startup info
    logger.info("Summarize MCP server starting...")
    logger.info(f"Platform: {platform.system()} ({platform.platform()})")
    logger.info(f"Temp directory: {CONFIG['temp_dir']}")
    logger.info(f"OpenAI API key: {'✓ Set' if api_key else '✗ Not set'}")
    logger.info(f"Audio player: {audio_player.name}")
    logger.info(f"Current voice: {current_state.voice}")
    logger.info(f"Current tone: {current_state.tone[:50]}...")


# Main entry point
def main():
    """Run the server."""
    # Run initialization before starting the server
    asyncio.run(initialize_server())
    
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()