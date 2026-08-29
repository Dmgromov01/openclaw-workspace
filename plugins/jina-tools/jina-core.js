// jina-core: чистые функции Jina AI (search / embeddings+rerank RAG)
// RAG передаёт выбранные фрагменты на внешние API Jina. Он намеренно выключен,
// пока владелец явно не подтвердит это через JINA_RAG_ALLOW_EXTERNAL=1.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const KEY_FILE = "/root/.openclaw/credentials/jina.key";
const CACHE_FILE = "/root/.openclaw/cache/jina_rag.json";
const DEFAULT_PATHS = ["/root/openclaw/MEMORY.md", "/root/openclaw/memory"];
const HTTP_TIMEOUT_MS = 30000;
const MAX_FILES = 200;
const MAX_FILE_BYTES = 2 * 1024 * 1024;
const MAX_CHUNKS = 1500;
const MAX_TOP_N = 5;
const MAX_SEARCH_CHARS = 12000;
const MAX_RAG_PAYLOAD_CHARS = 6000;
const MAX_RAG_SNIPPET_CHARS = 400;

function getKey() {
  return fs.readFileSync(KEY_FILE, "utf8").trim();
}

function externalRagAllowed() {
  return ["1", "true", "yes"].includes(
    String(process.env.JINA_RAG_ALLOW_EXTERNAL || "").trim().toLowerCase(),
  );
}

function requireExternalRagConsent() {
  if (!externalRagAllowed()) {
    throw new Error(
      "Jina RAG отключён: он передаёт фрагменты файлов внешнему API. " +
      "Для явного разрешения установите JINA_RAG_ALLOW_EXTERNAL=1.",
    );
  }
}

async function jinaGet(url) {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${getKey()}` },
    signal: AbortSignal.timeout(HTTP_TIMEOUT_MS),
  });
  if (!res.ok) {
    throw new Error(`Jina ${res.status}: ${(await res.text()).slice(0, 200)}`);
  }
  return res;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function jinaPost(url, body, retries = 3) {
  for (let attempt = 0; ; attempt += 1) {
    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${getKey()}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(HTTP_TIMEOUT_MS),
    });
    if (res.ok) return res.json();
    if (res.status === 429 && attempt < retries) {
      await sleep(20000 * (attempt + 1));
      continue;
    }
    throw new Error(`Jina ${res.status}: ${(await res.text()).slice(0, 200)}`);
  }
}

// ---- 2. Search: поиск + контент в одном ответе (markdown) ----
async function search(query, maxChars = MAX_SEARCH_CHARS) {
  const res = await jinaGet(`https://s.jina.ai/?q=${encodeURIComponent(query)}`);
  const text = await res.text();
  return text.slice(0, Math.max(1, Math.min(Number(maxChars) || MAX_SEARCH_CHARS, MAX_SEARCH_CHARS)));
}

// ---- 3+4. RAG: embeddings -> кандидаты -> rerank -> топ ----
function collectFiles(inputPaths) {
  const roots = inputPaths && inputPaths.length ? inputPaths : DEFAULT_PATHS;
  const files = [];
  const seen = new Set();

  const walk = (entry) => {
    if (files.length >= MAX_FILES) return;
    let stat;
    try {
      stat = fs.statSync(entry);
    } catch (_) {
      return;
    }
    if (stat.isDirectory()) {
      let names;
      try {
        names = fs.readdirSync(entry);
      } catch (_) {
        return;
      }
      for (const name of names) {
        walk(path.join(entry, name));
        if (files.length >= MAX_FILES) break;
      }
      return;
    }
    if (
      stat.isFile() &&
      stat.size <= MAX_FILE_BYTES &&
      /\.(md|txt|json|csv)$/i.test(entry) &&
      !seen.has(entry)
    ) {
      seen.add(entry);
      files.push(entry);
    }
  };

  for (const root of roots) {
    walk(root);
    if (files.length >= MAX_FILES) break;
  }
  return files.sort();
}

function chunkText(text, size = 800, overlap = 100) {
  const chunks = [];
  const actualSize = Math.max(100, Math.min(Number(size) || 800, 4000));
  const actualOverlap = Math.max(0, Math.min(Number(overlap) || 0, actualSize - 1));
  const step = actualSize - actualOverlap;
  for (let offset = 0; offset < text.length && chunks.length < MAX_CHUNKS; offset += step) {
    chunks.push(text.slice(offset, offset + actualSize));
  }
  return chunks;
}

function fileState(files) {
  return files.map((file) => {
    const stat = fs.statSync(file);
    return `${file}:${stat.mtimeMs}:${stat.size}`;
  }).join("|");
}

function cosine(a, b) {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let index = 0; index < a.length; index += 1) {
    dot += a[index] * b[index];
    normA += a[index] * a[index];
    normB += b[index] * b[index];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB) + 1e-9);
}

function readUsableCache(state) {
  try {
    const cache = JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
    if (
      cache.state === state &&
      Array.isArray(cache.chunks) &&
      Array.isArray(cache.vectors) &&
      cache.chunks.length === cache.vectors.length
    ) {
      return cache;
    }
  } catch (_) {
    // A stale or partial cache is safe to rebuild.
  }
  return null;
}

function writeCache(index) {
  fs.mkdirSync(path.dirname(CACHE_FILE), { recursive: true });
  const temporary = `${CACHE_FILE}.${process.pid}.${crypto.randomUUID()}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(index), { mode: 0o600 });
  fs.renameSync(temporary, CACHE_FILE);
}

async function getIndex(inputPaths) {
  requireExternalRagConsent();
  const files = collectFiles(inputPaths);
  if (!files.length) throw new Error("Не найдено доступных текстовых файлов для RAG.");
  const state = fileState(files);
  const cached = readUsableCache(state);
  if (cached) return cached;

  const chunks = [];
  for (const file of files) {
    let text;
    try {
      text = fs.readFileSync(file, "utf8");
    } catch (_) {
      continue;
    }
    for (const [index, chunk] of chunkText(text).entries()) {
      chunks.push({ text: chunk, source: `${file}#${index}` });
      if (chunks.length >= MAX_CHUNKS) break;
    }
    if (chunks.length >= MAX_CHUNKS) break;
  }
  if (!chunks.length) throw new Error("В доступных файлах нет текста для RAG.");

  const vectors = [];
  const batchSize = 20;
  for (let offset = 0; offset < chunks.length; offset += batchSize) {
    const batch = chunks.slice(offset, offset + batchSize).map((chunk) => chunk.text);
    const response = await jinaPost("https://api.jina.ai/v1/embeddings", {
      model: "jina-embeddings-v3",
      input: batch,
      task: "text-matching",
    });
    if (!Array.isArray(response.data) || response.data.length !== batch.length) {
      throw new Error("Jina вернула неполный ответ embeddings.");
    }
    vectors.push(...response.data.map((item) => item.embedding));
    if (offset + batchSize < chunks.length) await sleep(2500);
  }
  const index = { state, chunks, vectors };
  writeCache(index);
  return index;
}

async function rag(query, inputPaths, topN = 5) {
  requireExternalRagConsent();
  const normalizedQuery = String(query || "").trim();
  if (!normalizedQuery) throw new Error("Нужен непустой запрос для RAG.");
  const index = await getIndex(inputPaths);
  const queryResponse = await jinaPost("https://api.jina.ai/v1/embeddings", {
    model: "jina-embeddings-v3",
    input: [normalizedQuery],
    task: "text-matching",
  });
  const queryVector = queryResponse.data?.[0]?.embedding;
  if (!Array.isArray(queryVector)) throw new Error("Jina не вернула embedding для запроса.");

  const scored = index.chunks
    .map((chunk, indexPosition) => ({ ...chunk, sim: cosine(queryVector, index.vectors[indexPosition]) }))
    .sort((left, right) => right.sim - left.sim)
    .slice(0, 20);
  const reranked = await jinaPost("https://api.jina.ai/v1/rerank", {
    model: "jina-reranker-v2-base-multilingual",
    query: normalizedQuery,
    documents: scored.map((chunk) => chunk.text),
  });
  const requested = Math.max(1, Math.min(Number(topN) || 5, MAX_TOP_N));
  const results = (reranked.results || []).slice(0, requested)
    .filter((result) => Number.isInteger(result.index) && scored[result.index])
    .map((result) => ({
      score: Number(Number(result.relevance_score || 0).toFixed(3)),
      source: scored[result.index].source,
      snippet: scored[result.index].text.replace(/\s+/g, " ").slice(0, MAX_RAG_SNIPPET_CHARS),
    }));
  let payloadChars = 0;
  const boundedResults = results.filter((result) => {
    const nextChars = JSON.stringify(result).length;
    if (payloadChars + nextChars > MAX_RAG_PAYLOAD_CHARS) return false;
    payloadChars += nextChars;
    return true;
  });
  return { query: normalizedQuery, results: boundedResults };
}

module.exports = {
  search,
  rag,
  collectFiles,
  chunkText,
  getIndex,
  externalRagAllowed,
  requireExternalRagConsent,
};
