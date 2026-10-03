import { config } from './config.js';

let chain = Promise.resolve();

const keepAliveValue = () => {
  const raw = config.ollama.keepAlive;
  return /^-?\d+$/.test(String(raw)) ? Number(raw) : raw;
};

function request(messages, { json = false, numPredict = null, temperature = null } = {}) {
  const { url, model, numCtx, timeoutMs } = config.ollama;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  return fetch(`${url}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal: controller.signal,
    body: JSON.stringify({
      model,
      messages,
      stream: false,
      ...(json ? { format: 'json' } : {}),
      keep_alive: keepAliveValue(),
      options: {
        temperature: temperature ?? config.ollama.temperature,
        num_predict: numPredict ?? config.ollama.numPredict,
        num_ctx: numCtx,
      },
    }),
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`ollama ${res.status}: ${(await res.text()).slice(0, 200)}`);
      const data = await res.json();
      const text = (data.message?.content || '').trim();
      if (!text) throw new Error('ollama respondió vacío');
      return text;
    })
    .finally(() => clearTimeout(timer));
}

export function chat(messages) {
  const run = chain.then(() => request(messages));
  chain = run.catch(() => {});
  return run;
}

// Llamada chica con salida JSON estricta (extraccion de slots/intents).
export function chatJson(messages, opts = {}) {
  const run = chain.then(() =>
    request(messages, { json: true, numPredict: 160, temperature: 0, ...opts })
  );
  chain = run.catch(() => {});
  return run;
}

export async function isReady() {
  try {
    const res = await fetch(`${config.ollama.url}/api/tags`, {
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return false;
    const { models = [] } = await res.json();
    return models.some((m) => m.name === config.ollama.model || `${m.name}:latest` === config.ollama.model);
  } catch {
    return false;
  }
}
