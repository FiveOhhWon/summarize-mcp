#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import OpenAI from "openai";
import { promises as fs } from "fs";
import path from "path";
import { spawn } from "child_process";
import os from "os";


// Configuration
const CONFIG = {
  tempDir: path.join(os.tmpdir(), "summarize-mcp"),
  cleanupDelay: 10000, // 10 seconds
  defaultVoice: "coral" as const,
  defaultInstructions: "Keep the summary as short and concise as possible. Speak in a clear and informative tone.",
  stateFile: path.join(os.homedir(), ".summarize-mcp-state.json"),
} as const;

// Valid voices from OpenAI
const VALID_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"] as const;
type Voice = typeof VALID_VOICES[number];

// State interface
interface UserState {
  voice: Voice;
  tone: string;
}

// Default state
const DEFAULT_STATE: UserState = {
  voice: CONFIG.defaultVoice,
  tone: CONFIG.defaultInstructions,
};

// State management
let currentState: UserState = { ...DEFAULT_STATE };

// Load state from file
async function loadState(): Promise<void> {
  try {
    const data = await fs.readFile(CONFIG.stateFile, "utf-8");
    const parsed = JSON.parse(data);
    currentState = {
      voice: VALID_VOICES.includes(parsed.voice) ? parsed.voice : DEFAULT_STATE.voice,
      tone: parsed.tone || DEFAULT_STATE.tone,
    };
    logger.debug("Loaded state:", currentState);
  } catch (error) {
    // File doesn't exist or is invalid, use defaults
    logger.debug("No state file found, using defaults");
    currentState = { ...DEFAULT_STATE };
  }
}

// Save state to file
async function saveState(): Promise<void> {
  try {
    await fs.writeFile(CONFIG.stateFile, JSON.stringify(currentState, null, 2));
    logger.debug("Saved state:", currentState);
  } catch (error) {
    logger.error("Failed to save state:", error);
  }
}

// Input validation schemas
const PlaySummaryArgsSchema = z.object({
  summary: z.string().min(1).describe("The text summary to convert to speech and play"),
  voice: z.enum(VALID_VOICES)
    .optional()
    .describe("The voice to use for TTS (overrides saved preference)"),
  instructions: z.string()
    .optional()
    .describe("Instructions for how the text should be spoken (overrides saved tone)"),
});

const SetVoiceArgsSchema = z.object({
  voice: z.enum(VALID_VOICES)
    .describe("The voice to use for all future TTS requests"),
});

const SetToneArgsSchema = z.object({
  tone: z.string().min(1)
    .describe("The tone/instructions to use for all future TTS requests"),
});

// Error types
class TTSError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = "TTSError";
  }
}

// Logger
const logger = {
  info: (message: string, ...args: any[]) => {
    console.error(`[INFO] ${message}`, ...args);
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  },
  debug: (message: string, ...args: any[]) => {
    if (process.env.DEBUG === "true") {
      console.error(`[DEBUG] ${message}`, ...args);
    }
  },
};

// Ensure temp directory exists
async function ensureTempDir(): Promise<void> {
  try {
    await fs.mkdir(CONFIG.tempDir, { recursive: true });
  } catch (error) {
    logger.error("Failed to create temp directory", error);
    throw new TTSError("Failed to create temporary directory", "TEMP_DIR_ERROR");
  }
}

// Audio player interface
interface AudioPlayer {
  name: string;
  check(): Promise<boolean>;
  play(filePath: string): Promise<void>;
}

// macOS audio player using afplay
class AfplayPlayer implements AudioPlayer {
  name = "afplay (macOS)";

  async check(): Promise<boolean> {
    return new Promise((resolve) => {
      const check = spawn("which", ["afplay"], { stdio: "ignore" });
      check.on("close", (code) => {
        resolve(code === 0);
      });
      check.on("error", () => {
        resolve(false);
      });
    });
  }

  async play(filePath: string): Promise<void> {
    const player = spawn("afplay", [filePath], {
      detached: true,
      stdio: "ignore",
    });
    player.unref();
  }
}

// Windows audio player using PowerShell
class WindowsPlayer implements AudioPlayer {
  name = "Windows Media Player";

  async check(): Promise<boolean> {
    return process.platform === "win32";
  }

  async play(filePath: string): Promise<void> {
    // Use PowerShell to play audio in the background
    const script = `
      Add-Type -AssemblyName System.Windows.Forms
      $player = New-Object System.Media.SoundPlayer
      $player.SoundLocation = '${filePath.replace(/'/g, "''")}'
      $player.Play()
    `;
    
    const player = spawn("powershell", ["-Command", script], {
      detached: true,
      stdio: "ignore",
      shell: true,
    });
    player.unref();
  }
}

// Linux audio player using various tools
class LinuxPlayer implements AudioPlayer {
  name = "Linux audio player";
  private command: string | null = null;

  async check(): Promise<boolean> {
    if (process.platform !== "linux") return false;

    // Check for available audio players in order of preference
    const players = ["mpg123", "play", "aplay", "ffplay", "cvlc"];
    
    for (const player of players) {
      const available = await this.checkCommand(player);
      if (available) {
        this.command = player;
        logger.debug(`Found Linux audio player: ${player}`);
        return true;
      }
    }
    
    return false;
  }

  private async checkCommand(command: string): Promise<boolean> {
    return new Promise((resolve) => {
      const check = spawn("which", [command], { stdio: "ignore" });
      check.on("close", (code) => {
        resolve(code === 0);
      });
      check.on("error", () => {
        resolve(false);
      });
    });
  }

  async play(filePath: string): Promise<void> {
    if (!this.command) {
      throw new Error("No audio player available");
    }

    let args: string[] = [filePath];
    
    // Add specific arguments for different players
    if (this.command === "cvlc") {
      args = ["--play-and-exit", "--intf", "dummy", filePath];
    } else if (this.command === "ffplay") {
      args = ["-nodisp", "-autoexit", filePath];
    }

    const player = spawn(this.command, args, {
      detached: true,
      stdio: "ignore",
    });
    player.unref();
  }
}

// Generic fallback using node-speaker (would require additional dependency)
class FallbackPlayer implements AudioPlayer {
  name = "Fallback (open with default app)";

  async check(): Promise<boolean> {
    return true; // Always available as last resort
  }

  async play(filePath: string): Promise<void> {
    // Try to open with the system's default audio player
    const open = process.platform === "darwin" ? "open" : 
                 process.platform === "win32" ? "start" : "xdg-open";
    
    const player = spawn(open, [filePath], {
      detached: true,
      stdio: "ignore",
      shell: process.platform === "win32",
    });
    player.unref();
  }
}

// Get the appropriate audio player for the current platform
async function getAudioPlayer(): Promise<AudioPlayer | null> {
  const players: AudioPlayer[] = [
    new AfplayPlayer(),
    new WindowsPlayer(),
    new LinuxPlayer(),
    new FallbackPlayer(),
  ];

  for (const player of players) {
    const available = await player.check();
    if (available) {
      logger.info(`Using audio player: ${player.name}`);
      return player;
    }
  }

  return null;
}

// Clean up old files
async function cleanupOldFiles(): Promise<void> {
  try {
    const files = await fs.readdir(CONFIG.tempDir);
    const now = Date.now();
    
    for (const file of files) {
      if (file.startsWith("speech_") && file.endsWith(".mp3")) {
        const filePath = path.join(CONFIG.tempDir, file);
        try {
          const stats = await fs.stat(filePath);
          // Remove files older than 1 hour
          if (now - stats.mtimeMs > 3600000) {
            await fs.unlink(filePath);
            logger.debug(`Cleaned up old file: ${file}`);
          }
        } catch (error) {
          // File might be in use, ignore
        }
      }
    }
  } catch (error) {
    logger.debug("Cleanup error (non-critical)", error);
  }
}

// Main server setup
async function main() {
  // Initialize OpenAI client
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  if (!process.env.OPENAI_API_KEY) {
    logger.error("OPENAI_API_KEY environment variable is not set");
    throw new Error("OPENAI_API_KEY environment variable is required");
  }

  // Get appropriate audio player for the platform
  const audioPlayer = await getAudioPlayer();
  if (!audioPlayer) {
    logger.error("No audio player found for current platform");
    throw new Error("No audio player available. Please install an audio player (mpg123, sox, ffmpeg, or vlc on Linux)");
  }

  // Ensure temp directory exists
  await ensureTempDir();

  // Clean up old files on startup
  await cleanupOldFiles();

  // Load saved state
  await loadState();

  // Create MCP server
  const server = new Server(
    {
      name: "summarize-mcp",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register tool list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "play_summary",
          description: "Convert text summary to speech using OpenAI TTS and play it in the background. Keeps summaries under 100 words unless otherwise requested. Uses the saved voice and tone preferences unless overridden.",
          inputSchema: {
            type: "object",
            properties: {
              summary: {
                type: "string",
                description: "The text summary to convert to speech and play",
              },
              voice: {
                type: "string",
                enum: VALID_VOICES as unknown as [string, ...string[]],
                description: `The voice to use for TTS (optional, uses saved preference if not specified)`,
              },
              instructions: {
                type: "string",
                description: "Instructions for how the text should be spoken (optional, uses saved tone if not specified)",
              },
            },
            required: ["summary"],
          },
        },
        {
          name: "set_voice",
          description: "Set the default voice for all future text-to-speech conversions. Choose from: alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, or shimmer.",
          inputSchema: {
            type: "object",
            properties: {
              voice: {
                type: "string",
                enum: VALID_VOICES as unknown as [string, ...string[]],
                description: "The voice to use for all future TTS requests",
              },
            },
            required: ["voice"],
          },
        },
        {
          name: "set_tone",
          description: "Set the default tone/instructions for how text should be spoken in all future TTS requests.",
          inputSchema: {
            type: "object",
            properties: {
              tone: {
                type: "string",
                description: "The tone/instructions to use for all future TTS requests (e.g., 'Speak slowly and calmly', 'Be enthusiastic and energetic')",
              },
            },
            required: ["tone"],
          },
        },
      ],
    };
  });

  // Register tool call handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    if (name === "play_summary") {
      try {
        // Validate arguments
        const validatedArgs = PlaySummaryArgsSchema.parse(args);
        const { summary } = validatedArgs;
        
        // Use provided values or fall back to saved state
        const voice = validatedArgs.voice || currentState.voice;
        const instructions = validatedArgs.instructions || currentState.tone;

        logger.info(`Generating TTS for summary (${summary.length} chars) with voice: ${voice}`);

        // Generate unique filename with timestamp
        const timestamp = Date.now();
        const speechFile = path.join(CONFIG.tempDir, `speech_${timestamp}.mp3`);

        // Create TTS audio
        const mp3Response = await openai.audio.speech.create({
          model: "gpt-4o-mini-tts",
          voice: voice,
          input: summary,
          instructions: instructions,
        });

        // Convert to buffer and save
        const buffer = Buffer.from(await mp3Response.arrayBuffer());
        await fs.writeFile(speechFile, buffer);

        logger.info(`Audio file created: ${speechFile}`);

        // Play the audio in the background
        await audioPlayer.play(speechFile);
        logger.debug(`Audio playback started with ${audioPlayer.name}`);

        // Schedule cleanup
        setTimeout(async () => {
          try {
            await fs.unlink(speechFile);
            logger.debug(`Cleaned up audio file: ${speechFile}`);
          } catch (err) {
            // File might still be playing, ignore
            logger.debug(`Could not clean up file (might still be playing): ${speechFile}`);
          }
        }, CONFIG.cleanupDelay);

        return {
          content: [
            {
              type: "text",
              text: `✅ Summary converted to speech and playing in the background\n` +
                    `Voice: ${voice}\n` +
                    `Length: ${summary.length} characters`,
            },
          ],
        };
      } catch (error) {
        logger.error("Error in play_summary", error);

        if (error instanceof z.ZodError) {
          return {
            content: [
              {
                type: "text",
                text: `❌ Invalid arguments: ${error.errors.map(e => `${e.path.join(".")}: ${e.message}`).join(", ")}`,
              },
            ],
            isError: true,
          };
        }

        if (error instanceof TTSError) {
          return {
            content: [
              {
                type: "text",
                text: `❌ TTS Error (${error.code}): ${error.message}`,
              },
            ],
            isError: true,
          };
        }

        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        return {
          content: [
            {
              type: "text",
              text: `❌ Error playing summary: ${errorMessage}`,
            },
          ],
          isError: true,
        };
      }
    }

    if (name === "set_voice") {
      try {
        // Validate arguments
        const validatedArgs = SetVoiceArgsSchema.parse(args);
        const { voice } = validatedArgs;

        // Update state
        currentState.voice = voice;
        await saveState();

        logger.info(`Default voice changed to: ${voice}`);

        return {
          content: [
            {
              type: "text",
              text: `✅ Default voice set to: ${voice}\n\nAll future audio summaries will use this voice unless specifically overridden.`,
            },
          ],
        };
      } catch (error) {
        logger.error("Error in set_voice", error);

        if (error instanceof z.ZodError) {
          return {
            content: [
              {
                type: "text",
                text: `❌ Invalid arguments: ${error.errors.map(e => `${e.path.join(".")}: ${e.message}`).join(", ")}`,
              },
            ],
            isError: true,
          };
        }

        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        return {
          content: [
            {
              type: "text",
              text: `❌ Error setting voice: ${errorMessage}`,
            },
          ],
          isError: true,
        };
      }
    }

    if (name === "set_tone") {
      try {
        // Validate arguments
        const validatedArgs = SetToneArgsSchema.parse(args);
        const { tone } = validatedArgs;

        // Update state
        currentState.tone = tone;
        await saveState();

        logger.info(`Default tone changed`);

        return {
          content: [
            {
              type: "text",
              text: `✅ Default tone set to: "${tone}"\n\nAll future audio summaries will use this tone unless specifically overridden.`,
            },
          ],
        };
      } catch (error) {
        logger.error("Error in set_tone", error);

        if (error instanceof z.ZodError) {
          return {
            content: [
              {
                type: "text",
                text: `❌ Invalid arguments: ${error.errors.map(e => `${e.path.join(".")}: ${e.message}`).join(", ")}`,
              },
            ],
            isError: true,
          };
        }

        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        return {
          content: [
            {
              type: "text",
              text: `❌ Error setting tone: ${errorMessage}`,
            },
          ],
          isError: true,
        };
      }
    }

    return {
      content: [
        {
          type: "text",
          text: `Unknown tool: ${name}`,
        },
      ],
      isError: true,
    };
  });

  // Start server
  const transport = new StdioServerTransport();
  
  logger.info("Summarize MCP server starting...");
  logger.info(`Platform: ${process.platform} (${os.type()} ${os.release()})`);
  logger.info(`Temp directory: ${CONFIG.tempDir}`);
  logger.info(`OpenAI API key: ${process.env.OPENAI_API_KEY ? "✓ Set" : "✗ Not set"}`);
  logger.info(`Audio player: ${audioPlayer.name}`);
  logger.info(`Current voice: ${currentState.voice}`);
  logger.info(`Current tone: ${currentState.tone.substring(0, 50)}...`);
  
  await server.connect(transport);
  logger.info("Server connected and ready");
}

// Run the server
main().catch((error) => {
  logger.error("Fatal server error:", error);
  process.exit(1);
});