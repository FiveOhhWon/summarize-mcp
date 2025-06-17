// Simple test script for the summarize-mcp server
// Run with: OPENAI_API_KEY=your-key node test.js

import { spawn } from 'child_process';
import { createInterface } from 'readline';

const rl = createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('Starting summarize-mcp test...\n');

// Start the MCP server
const server = spawn('node', ['dist/index.js'], {
  env: { ...process.env },
  stdio: ['pipe', 'pipe', 'pipe']
});

// Handle server stderr (logs)
server.stderr.on('data', (data) => {
  console.log(`[SERVER LOG] ${data.toString().trim()}`);
});

// Send initialize request
const initRequest = {
  jsonrpc: '2.0',
  method: 'initialize',
  params: {
    protocolVersion: '0.1.0',
    capabilities: {}
  },
  id: 1
};

console.log('Sending initialize request...');
server.stdin.write(JSON.stringify(initRequest) + '\n');

// Wait a bit then send tools/list request
setTimeout(() => {
  const listRequest = {
    jsonrpc: '2.0',
    method: 'tools/list',
    params: {},
    id: 2
  };
  
  console.log('\nSending tools/list request...');
  server.stdin.write(JSON.stringify(listRequest) + '\n');
}, 1000);

// Wait a bit then send a test tool call
setTimeout(() => {
  const toolCallRequest = {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: 'play_summary',
      arguments: {
        summary: 'This is a test summary. The quick brown fox jumps over the lazy dog.',
        voice: 'nova',
        instructions: 'Speak clearly and at a moderate pace.'
      }
    },
    id: 3
  };
  
  console.log('\nSending play_summary tool call...');
  server.stdin.write(JSON.stringify(toolCallRequest) + '\n');
}, 2000);

// Handle server responses
let buffer = '';
server.stdout.on('data', (data) => {
  buffer += data.toString();
  const lines = buffer.split('\n');
  buffer = lines.pop() || '';
  
  for (const line of lines) {
    if (line.trim()) {
      try {
        const response = JSON.parse(line);
        console.log('\nServer response:', JSON.stringify(response, null, 2));
      } catch (e) {
        console.log('Non-JSON output:', line);
      }
    }
  }
});

// Clean up after 5 seconds
setTimeout(() => {
  console.log('\nTest complete. Shutting down...');
  server.kill();
  process.exit(0);
}, 5000);

server.on('error', (err) => {
  console.error('Server error:', err);
  process.exit(1);
});