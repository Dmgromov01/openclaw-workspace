import { create } from "zustand";
import { persist } from "zustand/middleware";
import { uid } from "@/lib/utils";
import type { TaskItem } from "@/lib/hub/types";

type TasksState = {
  tasks: TaskItem[];
  add: (text: string) => void;
  toggle: (id: string) => void;
  remove: (id: string) => void;
  clearDone: () => void;
};

const seed: TaskItem[] = [
  {
    id: "seed-1",
    text: "Согласовать спецификацию",
    done: false,
    createdAt: Date.now() - 3600_000,
  },
  {
    id: "seed-2",
    text: "Проверить выгрузку реестра",
    done: true,
    createdAt: Date.now() - 86_400_000,
  },
];

export const useTasks = create<TasksState>()(
  persist(
    (set) => ({
      tasks: seed,
      add: (text) => {
        const t = text.trim();
        if (!t) return;
        set((s) => ({
          tasks: [{ id: uid(), text: t.slice(0, 240), done: false, createdAt: Date.now() }, ...s.tasks],
        }));
      },
      toggle: (id) =>
        set((s) => ({
          tasks: s.tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t)),
        })),
      remove: (id) => set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),
      clearDone: () => set((s) => ({ tasks: s.tasks.filter((t) => !t.done) })),
    }),
    { name: "r2d2.tasks.v1" },
  ),
);
