#!/usr/bin/env python3
"""Simple test script for the summarize-mcp server.

Run with: OPENAI_API_KEY=your-key python test.py
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Dict, Any


async def read_stream(stream, prefix=""):
    """Read from a stream and print with prefix."""
    buffer = b""
    while True:
        try:
            chunk = await stream.read(1024)
            if not chunk:
                break
            
            buffer += chunk
            lines = buffer.split(b'\n')
            buffer = lines[-1]
            
            for line in lines[:-1]:
                if line.strip():
                    try:
                        data = json.loads(line)
                        print(f"\n{prefix}:", json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        print(f"{prefix} (raw):", line.decode('utf-8'))
        except Exception as e:
            print(f"Error reading stream: {e}")
            break


async def main():
    """Run the test."""
    print("Starting summarize-mcp test...\n")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Run with: OPENAI_API_KEY=your-key python test.py")
        sys.exit(1)
    
    # Start the MCP server
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "summarize_mcp",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={**os.environ}
    )
    
    # Start reading stderr (logs) in background
    stderr_task = asyncio.create_task(read_stream(process.stderr, "[SERVER LOG]"))
    
    # Start reading stdout (responses) in background
    stdout_task = asyncio.create_task(read_stream(process.stdout, "Server response"))
    
    # Send initialize request
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
    
    print("Sending initialize request...")
    process.stdin.write((json.dumps(init_request) + "\n").encode())
    await process.stdin.drain()
    
    # Wait a bit then send tools/list request
    await asyncio.sleep(1)
    
    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    print("\nSending tools/list request...")
    process.stdin.write((json.dumps(list_request) + "\n").encode())
    await process.stdin.drain()
    
    # Wait a bit then send a test tool call
    await asyncio.sleep(1)
    
    tool_call_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "play_summary",
            "arguments": {
                "summary": "This is a test summary. The quick brown fox jumps over the lazy dog.",
                "voice": "nova",
                "instructions": "Speak clearly and at a moderate pace."
            }
        },
        "id": 3
    }
    
    print("\nSending play_summary tool call...")
    process.stdin.write((json.dumps(tool_call_request) + "\n").encode())
    await process.stdin.drain()
    
    # Test set_voice
    await asyncio.sleep(1)
    
    set_voice_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "set_voice",
            "arguments": {
                "voice": "coral"
            }
        },
        "id": 4
    }
    
    print("\nSending set_voice tool call...")
    process.stdin.write((json.dumps(set_voice_request) + "\n").encode())
    await process.stdin.drain()
    
    # Test set_tone
    await asyncio.sleep(1)
    
    set_tone_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "set_tone",
            "arguments": {
                "tone": "Be enthusiastic and energetic!"
            }
        },
        "id": 5
    }
    
    print("\nSending set_tone tool call...")
    process.stdin.write((json.dumps(set_tone_request) + "\n").encode())
    await process.stdin.drain()
    
    # Wait for responses
    await asyncio.sleep(3)
    
    print("\nTest complete. Shutting down...")
    process.terminate()
    
    # Cancel background tasks
    stderr_task.cancel()
    stdout_task.cancel()
    
    try:
        await asyncio.wait_for(process.wait(), timeout=2)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
    
    print("Server stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Test error: {e}")
        sys.exit(1)