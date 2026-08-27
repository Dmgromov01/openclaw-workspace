type Entry<T> = { ts: number; data: T };

const store = new Map<string, Entry<unknown>>();

export async function cached<T>(key: string, ttlMs: number, fn: () => Promise<T>): Promise<T> {
  const hit = store.get(key) as Entry<T> | undefined;
  if (hit && Date.now() - hit.ts < ttlMs) return hit.data;
  const data = await fn();
  store.set(key, { ts: Date.now(), data });
  return data;
}

export async function fetchText(url: string, timeoutMs = 10000, maxBytes = 800_000) {
  const res = await fetch(url, {
    headers: { "User-Agent": "R2D2-Hub/1.0", Accept: "application/rss+xml, application/xml, text/xml, application/json, */*" },
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buf = await res.arrayBuffer();
  if (buf.byteLength > maxBytes) throw new Error("Ответ слишком большой");
  return new TextDecoder("utf-8", { fatal: false }).decode(buf);
}

export async function fetchJson<T>(url: string, timeoutMs = 10000): Promise<T> {
  const text = await fetchText(url, timeoutMs);
  return JSON.parse(text) as T;
}
