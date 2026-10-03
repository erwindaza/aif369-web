import 'dotenv/config';
import path from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const num = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const bool = (value, fallback) =>
  value === undefined || value === '' ? fallback : /^(1|true|yes|on)$/i.test(value);

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const knowledgeBase = process.env.KNOWLEDGE_DIR || path.join(rootDir, 'knowledge');
const tenantId = (process.env.TENANT || 'aif369').toLowerCase();
const tenantKnowledgeDir = path.join(knowledgeBase, tenantId);
// KNOWLEDGE_DIR explícito manda; si no, knowledge/<tenant> cuando existe.
const defaultKnowledgeDir = process.env.KNOWLEDGE_DIR
  ? knowledgeBase
  : existsSync(tenantKnowledgeDir)
    ? tenantKnowledgeDir
    : knowledgeBase;

export const config = {
  rootDir: rootDir,
  tenant: tenantId,
  dataDir: process.env.DATA_DIR || './data',
  healthPort: num(process.env.HEALTH_PORT, 8090),
  allowGroups: bool(process.env.ALLOW_GROUPS, false),
  contextMessages: num(process.env.CONTEXT_MESSAGES, 8),
  replyDelay: {
    min: num(process.env.REPLY_DELAY_MIN_MS, 700),
    max: num(process.env.REPLY_DELAY_MAX_MS, 2200),
  },
  instantReplyDelay: {
    min: num(process.env.INSTANT_REPLY_DELAY_MIN_MS, 120),
    max: num(process.env.INSTANT_REPLY_DELAY_MAX_MS, 400),
  },
  knowledge: {
    baseDir: knowledgeBase,
    dir: defaultKnowledgeDir,
    topK: num(process.env.KNOWLEDGE_TOP_K, 4),
    maxChars: num(process.env.KNOWLEDGE_MAX_CHARS, 2200),
    retriever: (process.env.KNOWLEDGE_RETRIEVER || 'lexical').toLowerCase(),
    embeddingModel: process.env.KNOWLEDGE_EMBED_MODEL || 'nomic-embed-text',
    cacheFile: process.env.KNOWLEDGE_EMBED_CACHE || path.join(rootDir, 'runtime', 'knowledge-embeddings.json'),
  },
  db: {
    host: process.env.PGHOST || '127.0.0.1',
    port: num(process.env.PGPORT, 5432),
    database: process.env.PGDATABASE || 'whatsapp_agent',
    user: process.env.PGUSER || 'wa_agent',
    password: process.env.PGPASSWORD || '',
  },
  extractor: (process.env.EXTRACTOR || 'auto').toLowerCase(), // auto | rules | model
  graphEnabled: bool(process.env.GRAPH_ENABLED, true),
  ollama: {
    url: (process.env.OLLAMA_URL || 'http://127.0.0.1:11434').replace(/\/$/, ''),
    model: process.env.OLLAMA_MODEL || 'gemma3:1b',
    keepAlive: process.env.OLLAMA_KEEP_ALIVE || '-1',
    temperature: num(process.env.OLLAMA_TEMPERATURE, 0.3),
    numPredict: num(process.env.OLLAMA_NUM_PREDICT, 110),
    numCtx: num(process.env.OLLAMA_NUM_CTX, 4096),
    timeoutMs: num(process.env.OLLAMA_TIMEOUT_MS, 20000),
  },
};

export const authDir = `${config.dataDir}/auth`;
