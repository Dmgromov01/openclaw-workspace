import { create } from "zustand";
import { persist } from "zustand/middleware";
import { uid } from "@/lib/utils";
import type { DictEntry } from "@/lib/hub/types";

type DictState = {
  entries: DictEntry[];
  add: (src: string, dst: string, pair: string) => void;
  remove: (id: string) => void;
};

export const useDictionary = create<DictState>()(
  persist(
    (set) => ({
      entries: [],
      add: (src, dst, pair) => {
        const s = src.trim();
        if (!s) return;
        set((st) => ({
          entries: [
            { id: uid(), src: s.slice(0, 500), dst: dst.trim().slice(0, 500), pair, createdAt: Date.now() },
            ...st.entries,
          ].slice(0, 200),
        }));
      },
      remove: (id) => set((st) => ({ entries: st.entries.filter((e) => e.id !== id) })),
    }),
    { name: "r2d2.dict.v1" },
  ),
);
