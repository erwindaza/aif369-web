// Benchmark de latencia del agente: mide tiempo real de respuesta por modelo.
// Uso: node scripts/bench-ollama.mjs [modelo...]
import { SYSTEM_PROMPT } from '../src/prompt.js';

const models = process.argv.slice(2).length ? process.argv.slice(2) : ['gemma3:4b', 'gemma3:1b'];
const url = (process.env.OLLAMA_URL || 'http://127.0.0.1:11434').replace(/\/$/, '');

const payload = (model) => ({
  model,
  stream: false,
  keep_alive: /^-?\d+$/.test(process.env.OLLAMA_KEEP_ALIVE || '-1')
    ? Number(process.env.OLLAMA_KEEP_ALIVE || -1)
    : process.env.OLLAMA_KEEP_ALIVE || '-1',
  messages: [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: 'Hola, quiero cotizar un proyecto de datos para mi empresa de retail' },
  ],
  options: { num_predict: 90, temperature: 0.3, num_ctx: 4096 },
});

for (const model of models) {
  const startedAt = Date.now();
  try {
    const res = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload(model)),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
    const data = await res.json();
    const total = (Date.now() - startedAt) / 1000;
    const tokens = data.eval_count || 0;
    const tps = data.eval_duration ? tokens / (data.eval_duration / 1e9) : 0;
    const promptT = data.prompt_eval_count || 0;
    console.log(`\n--- ${model}: ${total.toFixed(1)}s total | ${tokens} tokens salida | ${tps.toFixed(1)} tok/s | prompt ${promptT} tokens`);
    console.log(data.message?.content?.slice(0, 220) || '(vacío)');
  } catch (err) {
    console.log(`\n--- ${model}: FALLÓ ${err.message}`);
  }
}
