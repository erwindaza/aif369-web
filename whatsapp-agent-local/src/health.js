import { createServer } from 'node:http';
import { getMessageHealth, getState, getStateSince } from './state.js';
import { query } from './db.js';
import { getSignalErrorCount } from './signal-guard.js';
import { getKnowledgeStats } from './knowledge.js';
import { config } from './config.js';

const READY_STATES = new Set(['CONNECTED', 'READY']);

const dbStatus = async () => {
  try {
    await query('SELECT 1');
    return 'ok';
  } catch (err) {
    return `error: ${err.message}`;
  }
};

export async function startHealthServer(port) {
  const server = createServer(async (req, res) => {
    const url = (req.url || '/').split('?')[0];
    if (url !== '/health' && url !== '/ready') {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'not found' }));
      return;
    }

    const database = await dbStatus();
    const connection = getState();
    const signalErrors = getSignalErrorCount();
    const socketReady = READY_STATES.has(connection);
    const messages = getMessageHealth();
    const databaseOk = database === 'ok';
    const degraded = !databaseOk || !socketReady || signalErrors > 0;
    const healthy = databaseOk && socketReady && signalErrors === 0;

    const body =
      url === '/health'
        ? {
            status: degraded ? 'degraded' : 'ok',
            process: 'up',
            whatsapp: {
              connection,
              connection_since: getStateSince(),
              socket_ready: socketReady,
              messages_ok: signalErrors === 0,
              last_inbound_at: messages.lastInboundAt,
              last_outbound_at: messages.lastOutboundAt,
              signal_errors: signalErrors,
            },
            database,
            knowledge: getKnowledgeStats(),
            llm: { model: config.ollama.model, url: config.ollama.url },
            uptime_s: Math.round(process.uptime()),
          }
        : { ready: healthy, whatsapp: connection, database };

    res.writeHead(healthy ? 200 : 503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(body, null, 2));
  });

  await new Promise((resolve) => server.listen(port, '127.0.0.1', resolve));
  console.log(`[health] GET http://127.0.0.1:${port}/health y /ready`);
  return server;
}
