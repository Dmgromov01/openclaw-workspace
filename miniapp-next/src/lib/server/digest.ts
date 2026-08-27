import { createServerFn } from "@tanstack/react-start";
import { assertPublicHttps, stripHtml } from "@/lib/sanitize";
import { cached, fetchText } from "./cache";

export type DigestPost = { text: string; date?: string };
export type DigestBlock = { title: string; type: "rss" | "tg"; posts: DigestPost[]; error?: string };
export type DigestResult = { blocks: DigestBlock[]; total: number; ts: number };

type SourceIn = { type: "rss" | "tg"; name: string; title: string };

function tag(xml: string, name: string) {
  const cdata = xml.match(new RegExp(`<${name}[^>]*>\\s*<!\\[CDATA\\[([\\s\\S]*?)\\]\\]>\\s*</${name}>`, "i"));
  if (cdata?.[1]) return cdata[1];
  const plain = xml.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`, "i"));
  return plain?.[1] ?? "";
}

function parseFeed(xml: string): DigestPost[] {
  const items = [...xml.matchAll(/<item[\s\S]*?<\/item>/gi), ...xml.matchAll(/<entry[\s\S]*?<\/entry>/gi)];
  const out: DigestPost[] = [];
  for (const m of items.slice(0, 8)) {
    const chunk = m[0];
    const title = stripHtml(tag(chunk, "title"));
    const desc = stripHtml(tag(chunk, "description") || tag(chunk, "summary") || tag(chunk, "content"));
    const date = stripHtml(tag(chunk, "pubDate") || tag(chunk, "updated") || tag(chunk, "published"));
    const text = [title, desc].filter(Boolean).join(" — ").slice(0, 420);
    if (text) out.push({ text, date: date || undefined });
  }
  return out;
}

async function loadRss(url: string): Promise<DigestPost[]> {
  const safe = assertPublicHttps(url);
  const xml = await cached(`rss:${safe.href}`, 12 * 60_000, () => fetchText(safe.href, 9000, 600_000));
  return parseFeed(xml);
}

export const getDigest = createServerFn({ method: "POST" })
  .validator((data: { sources: SourceIn[] }) => data)
  .handler(async ({ data }): Promise<DigestResult> => {
    const sources = (data.sources ?? []).slice(0, 12);
    const blocks: DigestBlock[] = [];
    let total = 0;
    await Promise.all(
      sources.map(async (s) => {
        if (s.type === "tg") {
          blocks.push({
            title: s.title || s.name,
            type: "tg",
            posts: [],
            error: "Telegram-каналы подключаются через бота. Добавьте RSS-ленту источника.",
          });
          return;
        }
        try {
          const posts = await loadRss(s.name);
          total += posts.length;
          blocks.push({ title: s.title || s.name, type: "rss", posts });
        } catch (err) {
          blocks.push({
            title: s.title || s.name,
            type: "rss",
            posts: [],
            error: err instanceof Error ? err.message : "Не удалось загрузить",
          });
        }
      }),
    );
    const order = new Map(sources.map((s, i) => [s.title || s.name, i]));
    blocks.sort((a, b) => (order.get(a.title) ?? 0) - (order.get(b.title) ?? 0));
    return { blocks, total, ts: Date.now() };
  });
