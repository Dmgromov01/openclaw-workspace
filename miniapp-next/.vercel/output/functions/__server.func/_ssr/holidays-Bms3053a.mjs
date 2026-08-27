import { n as create, t as persist } from "../_libs/zustand.mjs";
import { m as uid } from "./router-BZC-qIbN.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/holidays-Bms3053a.js
var useCalendar = create()(persist((set) => ({
	events: [],
	add: (event) => {
		const summary = event.summary.trim().slice(0, 120);
		if (!summary) return;
		set((s) => ({ events: [...s.events, {
			...event,
			summary,
			id: uid(),
			source: "local"
		}] }));
	},
	remove: (id) => set((s) => ({ events: s.events.filter((e) => e.id !== id) }))
}), { name: "r2d2.calendar.v1" }));
/** Production calendar (RU) — extend per year without touching UI. */
var HOLIDAYS = [
	{
		date: "2026-01-01",
		summary: "Новый год"
	},
	{
		date: "2026-01-02",
		summary: "Новогодние каникулы"
	},
	{
		date: "2026-01-07",
		summary: "Рождество"
	},
	{
		date: "2026-02-23",
		summary: "День защитника Отечества"
	},
	{
		date: "2026-03-08",
		summary: "Международный женский день"
	},
	{
		date: "2026-05-01",
		summary: "Праздник Весны и Труда"
	},
	{
		date: "2026-05-09",
		summary: "День Победы"
	},
	{
		date: "2026-06-12",
		summary: "День России"
	},
	{
		date: "2026-11-04",
		summary: "День народного единства"
	}
];
function holidaysInRange(fromIso, toIso) {
	const from = fromIso.slice(0, 10);
	const to = toIso.slice(0, 10);
	return HOLIDAYS.filter((h) => h.date >= from && h.date <= to).map((h) => ({
		id: `holiday-${h.date}`,
		start: `${h.date}T00:00:00`,
		summary: h.summary,
		source: "holiday",
		allDay: true
	}));
}
//#endregion
export { useCalendar as n, holidaysInRange as t };
