import type { CalEvent } from "@/lib/hub/types";

/** Production calendar (RU) — extend per year without touching UI. */
const HOLIDAYS: { date: string; summary: string }[] = [
  { date: "2026-01-01", summary: "Новый год" },
  { date: "2026-01-02", summary: "Новогодние каникулы" },
  { date: "2026-01-07", summary: "Рождество" },
  { date: "2026-02-23", summary: "День защитника Отечества" },
  { date: "2026-03-08", summary: "Международный женский день" },
  { date: "2026-05-01", summary: "Праздник Весны и Труда" },
  { date: "2026-05-09", summary: "День Победы" },
  { date: "2026-06-12", summary: "День России" },
  { date: "2026-11-04", summary: "День народного единства" },
];

export function holidaysInRange(fromIso: string, toIso: string): CalEvent[] {
  const from = fromIso.slice(0, 10);
  const to = toIso.slice(0, 10);
  return HOLIDAYS.filter((h) => h.date >= from && h.date <= to).map((h) => ({
    id: `holiday-${h.date}`,
    start: `${h.date}T00:00:00`,
    summary: h.summary,
    source: "holiday" as const,
    allDay: true,
  }));
}
