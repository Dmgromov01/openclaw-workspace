//#region node_modules/.nitro/vite/services/ssr/assets/cache-DQJ8TyLZ.js
var store = /* @__PURE__ */ new Map();
async function cached(key, ttlMs, fn) {
	const hit = store.get(key);
	if (hit && Date.now() - hit.ts < ttlMs) return hit.data;
	const data = await fn();
	store.set(key, {
		ts: Date.now(),
		data
	});
	return data;
}
async function fetchText(url, timeoutMs = 1e4, maxBytes = 8e5) {
	const res = await fetch(url, {
		headers: {
			"User-Agent": "R2D2-Hub/1.0",
			Accept: "application/rss+xml, application/xml, text/xml, application/json, */*"
		},
		signal: AbortSignal.timeout(timeoutMs)
	});
	if (!res.ok) throw new Error(`HTTP ${res.status}`);
	const buf = await res.arrayBuffer();
	if (buf.byteLength > maxBytes) throw new Error("Ответ слишком большой");
	return new TextDecoder("utf-8", { fatal: false }).decode(buf);
}
async function fetchJson(url, timeoutMs = 1e4) {
	const text = await fetchText(url, timeoutMs);
	return JSON.parse(text);
}
//#endregion
export { fetchJson as n, fetchText as r, cached as t };
