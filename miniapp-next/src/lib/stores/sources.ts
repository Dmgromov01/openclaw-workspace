import { create } from "zustand";
import { persist } from "zustand/middleware";
import { uid } from "@/lib/utils";
import type { DigestSource } from "@/lib/hub/types";

export const DEFAULT_SOURCES: DigestSource[] = [
  { id: "meduza", type: "rss", name: "https://meduza.io/rss/all", title: "Медуза", enabled: true },
  { id: "rbc", type: "rss", name: "https://rssexport.rbc.ru/rbcnews/news/30/full.rss", title: "РБК", enabled: true },
  { id: "kommersant", type: "rss", name: "https://www.kommersant.ru/rss/news.xml", title: "Коммерсантъ", enabled: true },
  { id: "istories", type: "rss", name: "https://istories.media/rss/all.xml", title: "Важные истории", enabled: true },
];

type SourcesState = {
  sources: DigestSource[];
  add: (input: { type: DigestSource["type"]; name: string; title: string }) => string | null;
  remove: (id: string) => void;
  toggle: (id: string) => void;
  reset: () => void;
};

function normalizeSource(type: DigestSource["type"], name: string) {
  const raw = name.trim();
  if (type === "tg") {
    const handle = raw.replace(/^https?:\/\/t\.me\//i, "").replace(/^@/, "").split(/[/?#]/)[0] ?? "";
    if (!/^[a-zA-Z][a-zA-Z0-9_]{3,31}$/.test(handle)) return null;
    return handle;
  }
  try {
    const u = new URL(raw);
    if (u.protocol !== "https:") return null;
    return u.toString();
  } catch {
    return null;
  }
}

export const useSources = create<SourcesState>()(
  persist(
    (set, get) => ({
      sources: DEFAULT_SOURCES,
      add: (input) => {
        const name = normalizeSource(input.type, input.name);
        if (!name) return "Проверьте адрес источника";
        if (get().sources.some((s) => s.name === name)) return "Источник уже добавлен";
        if (get().sources.length >= 12) return "Не больше 12 источников";
        const title = (input.title || name).trim().slice(0, 60);
        set((s) => ({
          sources: [...s.sources, { id: uid(), type: input.type, name, title, enabled: true }],
        }));
        return null;
      },
      remove: (id) => set((s) => ({ sources: s.sources.filter((x) => x.id !== id) })),
      toggle: (id) =>
        set((s) => ({
          sources: s.sources.map((x) => (x.id === id ? { ...x, enabled: !x.enabled } : x)),
        })),
      reset: () => set({ sources: DEFAULT_SOURCES }),
    }),
    { name: "r2d2.sources.v1" },
  ),
);
