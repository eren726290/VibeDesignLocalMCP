/**
 * MCP Stdio Bridge - Converts stdio JSON-RPC to FastAPI HTTP calls
 * Used by Claude Code MCP client
 */
const readline = require('readline');
const http = require('http');

const HOST = 'localhost';
const PORT = 3004;
const DOC_ID = process.env.PAPER_DOC_ID || 'default';

function request(method, params = {}) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params,
    });

    const options = {
      hostname: HOST,
      port: PORT,
      path: '/mcp',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'x-paper-doc-id': DOC_ID,
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(data);
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

rl.on('line', async (line) => {
  try {
    const msg = JSON.parse(line);
    const result = await request(msg.method, msg.params);
    console.log(JSON.stringify(result));
  } catch (err) {
    console.error(JSON.stringify({ error: { code: -32603, message: err.message } }));
  }
});
