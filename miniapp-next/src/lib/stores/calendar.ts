import { create } from "zustand";
import { persist } from "zustand/middleware";
import { uid } from "@/lib/utils";
import type { CalEvent } from "@/lib/hub/types";

type CalState = {
  events: CalEvent[];
  add: (event: Omit<CalEvent, "id" | "source">) => void;
  remove: (id: string) => void;
};

export const useCalendar = create<CalState>()(
  persist(
    (set) => ({
      events: [],
      add: (event) => {
        const summary = event.summary.trim().slice(0, 120);
        if (!summary) return;
        set((s) => ({
          events: [
            ...s.events,
            { ...event, summary, id: uid(), source: "local" as const },
          ],
        }));
      },
      remove: (id) => set((s) => ({ events: s.events.filter((e) => e.id !== id) })),
    }),
    { name: "r2d2.calendar.v1" },
  ),
);
