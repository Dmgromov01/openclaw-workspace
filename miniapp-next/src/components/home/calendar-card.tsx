import { useMemo, useState } from "react";
import { CalendarDays, Plus } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useCalendar } from "@/lib/stores/calendar";
import { holidaysInRange } from "@/lib/calendar/holidays";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ServiceRow } from "@/components/shell/service-row";
import { haptic } from "@/lib/haptic";
import { formatDayLabel } from "@/lib/utils";
import type { CalEvent } from "@/lib/hub/types";

function upcomingDays(n: number) {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

export function CalendarCard() {
  const navigate = useNavigate();
  const events = useCalendar((s) => s.events);
  const add = useCalendar((s) => s.add);
  const [draft, setDraft] = useState("");
  const [when, setWhen] = useState("");

  const days = useMemo(() => {
    const list = upcomingDays(7);
    const from = list[0]!.toISOString();
    const to = new Date(list[6]!.getTime() + 86400000).toISOString();
    const holidays = holidaysInRange(from, to);
    const all: CalEvent[] = [...events, ...holidays];
    return list.map((d) => {
      const key = d.toISOString().slice(0, 10);
      const dayEvents = all
        .filter((e) => e.start.slice(0, 10) === key)
        .sort((a, b) => a.start.localeCompare(b.start));
      return { date: d, key, label: formatDayLabel(d), events: dayEvents };
    });
  }, [events]);

  const visible = days.filter((d) => d.events.length > 0);

  const addQuick = () => {
    const summary = draft.trim();
    if (!summary) return;
    const start = when || new Date(Date.now() + 3600_000).toISOString().slice(0, 16);
    add({ start: new Date(start).toISOString(), summary });
    setDraft("");
    haptic("medium");
  };

  return (
    <Card>
      <ServiceRow
        icon={<CalendarDays className="size-5" />}
        title="Календарь"
        status="7 дней · локальные события и праздники"
        onClick={() => {
          haptic();
          navigate({ to: "/calendar" });
        }}
      />
      <div className="space-y-2 border-t border-border px-4 py-3">
        {visible.length === 0 ? (
          <div className="py-2 text-center text-xs text-muted-foreground">На ближайшие 7 дней событий нет.</div>
        ) : (
          visible.map((d) => (
            <div key={d.key} className="rounded-xl border border-border bg-muted p-3">
              <div className="mb-1.5 text-xs font-bold uppercase tracking-wide text-muted-foreground">{d.label}</div>
              <div className="space-y-1.5">
                {d.events.map((ev) => (
                  <div key={ev.id} className="flex items-start gap-2">
                    <span className="mt-0.5 shrink-0 font-mono text-xs font-extrabold tabular-nums text-accent">
                      {ev.allDay ? "весь день" : ev.start.slice(11, 16)}
                    </span>
                    <div className="min-w-0 flex-1 text-sm font-semibold leading-snug">{ev.summary}</div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
        <div className="flex gap-2 pt-1">
          <Input
            placeholder="Новое событие…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") addQuick();
            }}
          />
          <input
            type="datetime-local"
            value={when}
            onChange={(e) => setWhen(e.target.value)}
            className="h-11 w-[9.5rem] rounded-xl border border-border bg-muted px-2 text-xs text-foreground"
            aria-label="Дата и время"
          />
          <Button type="button" variant="solid" size="icon" onClick={addQuick} aria-label="Добавить событие">
            <Plus className="size-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
