// jina-core: чистые функции Jina AI (search / embeddings+rerank RAG)
// Отдельный модуль, чтобы тестировать без OpenClaw.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const KEY_FILE = "/root/.openclaw/credentials/jina.key";
const CACHE_FILE = "/root/.openclaw/cache/jina_rag.json";

const DEFAULT_PATHS = ["/root/openclaw/MEMORY.md", "/root/openclaw/memory"];

function getKey() {
  return fs.readFileSync(KEY_FILE, "utf8").trim();
}

async function jinaGet(url) {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${getKey()}` },
  });
  if (!res.ok) {
    throw new Error(`Jina ${res.status}: ${(await res.text()).slice(0, 200)}`);
  }
  return res;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function jinaPost(url, body, retries = 3) {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${getKey()}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) return res.json();
    if (res.status === 429 && attempt < retries) {
      const wait = 20000 * (attempt + 1); // 20s, 40s, 60s
      await sleep(wait);
      continue;
    }
    throw new Error(`Jina ${res.status}: ${(await res.text()).slice(0, 200)}`);
  }
}

// ---- 2. Search: поиск + контент в одном ответе (markdown) ----
async function search(query, maxChars = 15000) {
  const res = await jinaGet(`https://s.jina.ai/?q=${encodeURIComponent(query)}`);
  const text = await res.text();
  return text.slice(0, maxChars);
}

// ---- 3+4. RAG: embeddings -> кандидаты -> rerank -> топ ----
function collectFiles(inputPaths) {
  const paths = inputPaths && inputPaths.length ? inputPaths : DEFAULT_PATHS;
  const files = [];
  const walk = (p) => {
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      for (const f of fs.readdirSync(p)) walk(path.join(p, f));
    } else if (/\.(md|txt|json|csv)$/i.test(p)) {
      files.push(p);
    }
  };
  for (const p of paths) walk(p);
  return files.sort();
}

function chunkText(text, size = 800, overlap = 100) {
  const chunks = [];
  for (let i = 0; i < text.length; i += size - overlap) {
    chunks.push(text.slice(i, i + size));
  }
  return chunks;
}

function fileState(files) {
  return files.map((f) => `${f}:${fs.statSync(f).mtimeMs}`).join("|");
}

function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-9);
}

async function getIndex(inputPaths) {
  const files = collectFiles(inputPaths);
  const state = fileState(files);
  if (fs.existsSync(CACHE_FILE)) {
    try {
      const cache = JSON.parse(fs.readFileSync(CACHE_FILE, "utf8"));
      if (cache.state === state) return cache;
    } catch (_) { /* пересоберём */ }
  }
  const chunks = [];
  for (const f of files) {
    const text = fs.readFileSync(f, "utf8");
    chunkText(text).forEach((c, i) => chunks.push({ text: c, source: `${f}#${i}` }));
  }
  const vectors = [];
  const BATCH = 20; // 100K токенов/мин лимит; память ~60K => дробим и ждём
  for (let i = 0; i < chunks.length; i += BATCH) {
    const batch = chunks.slice(i, i + BATCH).map((c) => c.text);
    const r = await jinaPost("https://api.jina.ai/v1/embeddings", {
      model: "jina-embeddings-v3",
      input: batch,
      task: "text-matching",
    });
    vectors.push(...r.data.map((d) => d.embedding));
    if (i + BATCH < chunks.length) await sleep(2500);
  }
  const idx = { state, chunks, vectors };
  fs.mkdirSync(path.dirname(CACHE_FILE), { recursive: true });
  fs.writeFileSync(CACHE_FILE, JSON.stringify(idx));
  return idx;
}

async function rag(query, inputPaths, topN = 5) {
  const idx = await getIndex(inputPaths);
  const qr = await jinaPost("https://api.jina.ai/v1/embeddings", {
    model: "jina-embeddings-v3",
    input: [query],
    task: "text-matching",
  });
  const qv = qr.data[0].embedding;
  const scored = idx.chunks
    .map((c, i) => ({ ...c, sim: cosine(qv, idx.vectors[i]) }))
    .sort((a, b) => b.sim - a.sim)
    .slice(0, 20);
  const rr = await jinaPost("https://api.jina.ai/v1/rerank", {
    model: "jina-reranker-v2-base-multilingual",
    query,
    documents: scored.map((c) => c.text),
  });
  const results = rr.results.slice(0, topN).map((r) => ({
    score: Number(r.relevance_score.toFixed(3)),
    source: scored[r.index].source,
    snippet: scored[r.index].text.replace(/\s+/g, " ").slice(0, 400),
  }));
  return { query, results };
}

module.exports = { search, rag, collectFiles, chunkText, getIndex };
