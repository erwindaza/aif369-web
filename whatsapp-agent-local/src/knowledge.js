import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { config } from './config.js';

const STOPWORDS = new Set(
  (
    'de la que el en y a los del se las por un para con no una su al lo como más pero sus le ya ' +
    'o este sí porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo ' +
    'nos durante les uno les ni contra otros ese eso ante ellos e esto mí antes algunos qué unos ' +
    'yo él otra otro ellas nos ti tus tú él sea pues nada vosotros os yo algunas alguno unos ' +
    'the and for with you your our are was were this that from have has can will would should ' +
    'is are of to in on it be do does did i we they he she what how when who which or if not ' +
    'ser estar tiene tener puede pueden quiero necesito hola gracias buenos dias tardes noches ' +
    'usted ustedes hacen hace hacer pueden podrian cual cuales cuanto cuanto'
  ).split(/\s+/)
);

const normalize = (text) =>
  String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9ñ\s]/g, ' ');

export function tokenize(text) {
  return normalize(text)
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w));
}

const bigrams = (tokens) => {
  const out = [];
  for (let i = 0; i < tokens.length - 1; i += 1) out.push(`${tokens[i]} ${tokens[i + 1]}`);
  return out;
};

const states = new Map(); // dir -> knowledge base

function parseDocument(docName, raw) {
  const lines = raw.split(/\r?\n/);
  const docTitle = (lines.find((l) => l.startsWith('# ')) || `# ${docName}`).replace(/^#\s+/, '').trim();
  const chunks = [];
  let keywords = '';
  let heading = null;
  let buffer = [];

  const flush = () => {
    if (!heading) return;
    const body = buffer.join('\n').trim();
    if (/^t[eé]rminos clave$/i.test(heading)) {
      keywords = body;
      heading = null;
      buffer = [];
      return;
    }
    if (body) {
      const text = `## ${heading}\n${body}`;
      const tokens = tokenize(`${docTitle} ${heading} ${body}`);
      chunks.push({
        id: `${docName}#${chunks.length}`,
        doc: docName,
        title: docTitle,
        heading,
        text,
        tokens: new Set(tokens),
        tokenList: tokens,
        keywords: tokenize(keywords || ''),
      });
    }
    heading = null;
    buffer = [];
  };

  for (const line of lines) {
    if (/^##\s+/.test(line)) {
      flush();
      heading = line.replace(/^##\s+/, '').trim();
      buffer = [];
    } else if (heading) {
      buffer.push(line);
    }
  }
  flush();
  return { docName, docTitle, chunks, keywords: tokenize(keywords) };
}

export async function loadKnowledge({ force = false, dir = config.knowledge.dir } = {}) {
  const existing = states.get(dir);
  if (existing && !force) return existing;
  let entries = [];
  try {
    entries = (await readdir(dir)).filter((f) => f.endsWith('.md')).sort();
  } catch {
    entries = [];
  }

  const docs = [];
  const chunks = [];
  for (const file of entries) {
    const raw = await readFile(path.join(dir, file), 'utf8').catch(() => '');
    if (!raw.trim()) continue;
    const parsed = parseDocument(file.replace(/\.md$/, ''), raw);
    docs.push({ name: parsed.docName, title: parsed.docTitle, chunks: parsed.chunks.length });
    for (const c of parsed.chunks) {
      c.keywords = parsed.keywords;
      chunks.push(c);
    }
  }

  const kb = {
    loadedAt: new Date().toISOString(),
    dir,
    docs,
    chunks,
    retriever: config.knowledge.retriever === 'embedding' ? 'embedding' : 'lexical',
    embeddings: null,
  };
  states.set(dir, kb);

  if (kb.retriever === 'embedding') {
    await ensureEmbeddings(kb).catch((err) => {
      console.log(`[knowledge][warn] embeddings no disponibles (${err.message}); se usa retrieval lexico`);
      kb.retriever = 'lexical';
    });
  }

  console.log(`[knowledge] ${docs.length} documentos, ${chunks.length} fragmentos (${kb.retriever}) dir=${dir}`);
  return kb;
}

async function getState(dir = config.knowledge.dir) {
  return states.get(dir) || (await loadKnowledge({ dir }));
}

export const getKnowledgeStats = (dir = config.knowledge.dir) => {
  const kb = states.get(dir);
  return kb
    ? { docs: kb.docs.length, chunks: kb.chunks.length, retriever: kb.retriever, loaded_at: kb.loadedAt, dir }
    : { docs: 0, chunks: 0, retriever: 'none', loaded_at: null, dir };
};

function scoreLexical(chunk, queryTokens, queryBigrams) {
  let score = 0;
  let matched = 0;
  const headingNorm = normalize(chunk.heading);
  const keywords = new Set(chunk.keywords);

  for (const token of queryTokens) {
    if (!chunk.tokens.has(token) && !keywords.has(token)) continue;
    matched += 1;
    score += 1;
    if (headingNorm.includes(token)) score += 2;
    if (keywords.has(token)) score += 1.5;
  }

  if (matched === 0) return 0;

  const rawNorm = normalize(chunk.text);
  for (const bg of queryBigrams) {
    if (rawNorm.includes(bg)) score += 2;
  }

  const coverage = matched / queryTokens.length;
  const lengthPenalty = 1 / (1 + chunk.tokenList.length / 400);
  return score * (0.4 + 0.6 * coverage) * (0.6 + 0.4 * lengthPenalty);
}

async function ensureEmbeddings(kb) {
  const { chunks } = kb;
  const cache = await readEmbedCache();
  const byHash = new Map(cache.entries?.map((e) => [e.hash, e.vector]) || []);
  let missing = 0;

  for (const chunk of chunks) {
    const hash = createHash('sha1').update(chunk.text).digest('hex');
    chunk.hash = hash;
    const cached = byHash.get(hash);
    if (cached) {
      chunk.vector = cached;
    } else {
      missing += 1;
    }
  }

  if (missing > 0) {
    for (const chunk of chunks) {
      if (chunk.vector) continue;
      chunk.vector = await embed(chunk.text);
      chunk.hash = createHash('sha1').update(chunk.text).digest('hex');
    }
    await writeEmbedCache(
      chunks.filter((c) => c.vector).map((c) => ({ hash: c.hash, vector: c.vector }))
    );
  }

  kb.embeddings = { model: config.knowledge.embeddingModel, count: chunks.filter((c) => c.vector).length };
}

async function readEmbedCache() {
  try {
    return JSON.parse(await readFile(config.knowledge.cacheFile, 'utf8'));
  } catch {
    return { entries: [] };
  }
}

async function writeEmbedCache(entries) {
  try {
    await mkdir(path.dirname(config.knowledge.cacheFile), { recursive: true });
    await writeFile(config.knowledge.cacheFile, JSON.stringify({ entries }));
  } catch (err) {
    console.log(`[knowledge][warn] no se pudo guardar cache de embeddings: ${err.message}`);
  }
}

async function embed(text) {
  const res = await fetch(`${config.ollama.url}/api/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(15000),
    body: JSON.stringify({ model: config.knowledge.embeddingModel, prompt: text }),
  });
  if (!res.ok) throw new Error(`ollama embeddings ${res.status}`);
  const data = await res.json();
  if (!Array.isArray(data.embedding)) throw new Error('embedding invalido');
  return data.embedding;
}

const cosine = (a, b) => {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) || 1);
};

export async function retrieve(query, opts = {}) {
  const kb = await getState(opts.dir);
  const topK = opts.topK || config.knowledge.topK;
  const queryText = String(query || '').trim();
  if (!queryText || kb.chunks.length === 0) return [];

  if (kb.retriever === 'embedding') {
    const qv = await embed(queryText);
    return kb.chunks
      .map((chunk) => ({ chunk, score: cosine(qv, chunk.vector || []) }))
      .filter((r) => r.score > 0.15)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK)
      .map((r) => ({ ...r, source: 'embedding' }));
  }

  const queryTokens = tokenize(queryText);
  if (queryTokens.length === 0) return [];
  const queryBigrams = bigrams(queryTokens);
  return kb.chunks
    .map((chunk) => ({ chunk, score: scoreLexical(chunk, queryTokens, queryBigrams) }))
    .filter((r) => r.score >= 1)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK)
    .map((r) => ({ ...r, source: 'lexical' }));
}

export function formatContext(hits, maxChars = config.knowledge.maxChars) {
  if (!hits.length) return '';
  let out = '';
  for (const hit of hits) {
    const block = `${hit.chunk.title} > ${hit.chunk.text.replace(/^##\s+/, '')}\n`;
    if (out.length + block.length > maxChars) break;
    out += block;
  }
  return out.trim();
}

export async function buildKnowledgeContext(query, opts = {}) {
  const startedAt = Date.now();
  const hits = await retrieve(query, opts);
  return {
    hits,
    context: formatContext(hits),
    retrievalMs: Date.now() - startedAt,
  };
}
