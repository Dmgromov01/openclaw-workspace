import { useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { useCalendar } from "@/lib/stores/calendar";
import { holidaysInRange } from "@/lib/calendar/holidays";
import { AppShell } from "@/components/shell/app-shell";
import { Header } from "@/components/shell/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { haptic } from "@/lib/haptic";
import { formatDayLabel } from "@/lib/utils";
import type { CalEvent } from "@/lib/hub/types";

export function CalendarView() {
  const events = useCalendar((s) => s.events);
  const add = useCalendar((s) => s.add);
  const remove = useCalendar((s) => s.remove);
  const [summary, setSummary] = useState("");
  const [when, setWhen] = useState("");

  const days = useMemo(() => {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const list = Array.from({ length: 14 }, (_, i) => {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      return d;
    });
    const from = list[0]!.toISOString();
    const to = new Date(list.at(-1)!.getTime() + 86400000).toISOString();
    const all: CalEvent[] = [...events, ...holidaysInRange(from, to)];
    return list.map((d) => {
      const key = d.toISOString().slice(0, 10);
      return {
        key,
        label: formatDayLabel(d),
        events: all.filter((e) => e.start.slice(0, 10) === key).sort((a, b) => a.start.localeCompare(b.start)),
      };
    });
  }, [events]);

  return (
    <AppShell>
      <Header title="Календарь" subtitle="14 дней · локально + праздники" backTo="/" />
      <div className="space-y-3 px-4">
        <Card className="space-y-2 p-4">
          <Input value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Событие" />
          <div className="flex gap-2">
            <input
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              className="h-11 flex-1 rounded-xl border border-border bg-muted px-3 text-sm"
            />
            <Button
              size="icon"
              onClick={() => {
                if (!summary.trim() || !when) return;
                add({ start: new Date(when).toISOString(), summary });
                setSummary("");
                haptic("medium");
              }}
            >
              <Plus className="size-4" />
            </Button>
          </div>
        </Card>
        {days.map((d) => (
          <Card key={d.key} className="p-4">
            <div className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">{d.label}</div>
            {d.events.length === 0 ? (
              <div className="text-sm text-muted-foreground">Нет событий</div>
            ) : (
              <div className="space-y-2">
                {d.events.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-2">
                    <span className="mt-0.5 w-16 shrink-0 font-mono text-xs font-extrabold tabular-nums text-accent">
                      {ev.allDay ? "день" : ev.start.slice(11, 16)}
                    </span>
                    <div className="min-w-0 flex-1 text-sm font-semibold">{ev.summary}</div>
                    {ev.source === "local" ? (
                      <button
                        type="button"
                        onClick={() => remove(ev.id)}
                        className="grid size-8 place-items-center text-muted-foreground"
                        aria-label="Удалить"
                      >
                        <X className="size-4" />
                      </button>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
    </AppShell>
  );
}
