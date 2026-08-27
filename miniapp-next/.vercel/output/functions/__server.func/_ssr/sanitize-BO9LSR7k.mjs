//#region node_modules/.nitro/vite/services/ssr/assets/sanitize-BO9LSR7k.js
var ENTITY = {
	amp: "&",
	lt: "<",
	gt: ">",
	quot: "\"",
	apos: "'",
	nbsp: " ",
	ndash: "–",
	mdash: "—",
	laquo: "«",
	raquo: "»",
	hellip: "…"
};
function decodeEntities(input) {
	return input.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (_, code) => {
		if (code[0] === "#") {
			const n = code[1]?.toLowerCase() === "x" ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
			return Number.isFinite(n) ? String.fromCodePoint(n) : "";
		}
		return ENTITY[code.toLowerCase()] ?? "";
	});
}
function stripHtml(input) {
	return decodeEntities(input).replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}
var PRIVATE_HOST = /^(localhost|127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|0\.0\.0\.0|169\.254\.\d+\.\d+|::1|\[::1\])$/i;
function assertPublicHttps(raw) {
	let url;
	try {
		url = new URL(raw);
	} catch {
		throw new Error("Некорректный URL");
	}
	if (url.protocol !== "https:") throw new Error("Разрешён только HTTPS");
	const host = url.hostname.replace(/^\[|\]$/g, "");
	if (PRIVATE_HOST.test(host) || host.endsWith(".local") || host.endsWith(".internal")) throw new Error("Приватные адреса запрещены");
	return url;
}
function clampText(input, max) {
	const t = input.trim();
	if (t.length <= max) return t;
	return t.slice(0, max);
}
//#endregion
export { stripHtml as i, clampText as n, decodeEntities as r, assertPublicHttps as t };
