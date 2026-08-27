import { Trash2, X } from "lucide-react";
import { useTasks } from "@/lib/stores/tasks";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Button } from "@/components/ui/button";
import { haptic } from "@/lib/haptic";

export function ArchiveView() {
  const { tasks, toggle, remove, clearDone } = useTasks();
  const done = tasks.filter((t) => t.done);

  return (
    <AppShell>
      <Header
        title="Архив дел"
        subtitle="Выполненные задачи"
        backTo="/"
        right={
          done.length > 0 ? (
            <Button
              variant="secondary"
              size="icon-sm"
              aria-label="Очистить архив"
              onClick={() => {
                haptic("heavy");
                clearDone();
              }}
            >
              <Trash2 className="size-4" />
            </Button>
          ) : undefined
        }
      />
      <div className="space-y-2.5 px-4">
        {done.map((t) => (
          <div
            key={t.id}
            className="flex items-center justify-between gap-2 rounded-xl border border-border bg-card p-3.5"
          >
            <button
              type="button"
              className="flex min-w-0 flex-1 items-center gap-3 text-left"
              onClick={() => {
                haptic();
                toggle(t.id);
              }}
            >
              <div className="grid size-6 shrink-0 place-items-center rounded-lg bg-success text-xs font-bold text-accent-foreground">
                ✓
              </div>
              <span className="truncate text-sm font-semibold text-muted-foreground line-through">{t.text}</span>
            </button>
            <button
              type="button"
              onClick={() => remove(t.id)}
              className="grid size-9 place-items-center text-muted-foreground hover:text-destructive"
              aria-label="Удалить"
            >
              <X className="size-4" />
            </button>
          </div>
        ))}
        {done.length === 0 ? (
          <div className="rounded-xl border border-border bg-card px-6 py-10 text-center text-sm text-muted-foreground">
            В архиве нет выполненных задач.
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
