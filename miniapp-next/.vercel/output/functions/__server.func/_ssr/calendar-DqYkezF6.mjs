import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { f as Plus, t as X } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { f as haptic, n as Input, s as Button, u as formatDayLabel } from "./router-BZC-qIbN.mjs";
import { n as useCalendar, t as holidaysInRange } from "./holidays-Bms3053a.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/calendar-DqYkezF6.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function CalendarView() {
	const events = useCalendar((s) => s.events);
	const add = useCalendar((s) => s.add);
	const remove = useCalendar((s) => s.remove);
	const [summary, setSummary] = (0, import_react.useState)("");
	const [when, setWhen] = (0, import_react.useState)("");
	const days = (0, import_react.useMemo)(() => {
		const start = /* @__PURE__ */ new Date();
		start.setHours(0, 0, 0, 0);
		const list = Array.from({ length: 14 }, (_, i) => {
			const d = new Date(start);
			d.setDate(start.getDate() + i);
			return d;
		});
		const from = list[0].toISOString();
		const to = new Date(list.at(-1).getTime() + 864e5).toISOString();
		const all = [...events, ...holidaysInRange(from, to)];
		return list.map((d) => {
			const key = d.toISOString().slice(0, 10);
			return {
				key,
				label: formatDayLabel(d),
				events: all.filter((e) => e.start.slice(0, 10) === key).sort((a, b) => a.start.localeCompare(b.start))
			};
		});
	}, [events]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Календарь",
		subtitle: "14 дней · локально + праздники",
		backTo: "/"
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
			className: "space-y-2 p-4",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
				value: summary,
				onChange: (e) => setSummary(e.target.value),
				placeholder: "Событие"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex gap-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
					type: "datetime-local",
					value: when,
					onChange: (e) => setWhen(e.target.value),
					className: "h-11 flex-1 rounded-xl border border-border bg-muted px-3 text-sm"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "icon",
					onClick: () => {
						if (!summary.trim() || !when) return;
						add({
							start: new Date(when).toISOString(),
							summary
						});
						setSummary("");
						haptic("medium");
					},
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "size-4" })
				})]
			})]
		}), days.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
			className: "p-4",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground",
				children: d.label
			}), d.events.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "text-sm text-muted-foreground",
				children: "Нет событий"
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-2",
				children: d.events.map((ev) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-start gap-2",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "mt-0.5 w-16 shrink-0 font-mono text-xs font-extrabold tabular-nums text-accent",
							children: ev.allDay ? "день" : ev.start.slice(11, 16)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "min-w-0 flex-1 text-sm font-semibold",
							children: ev.summary
						}),
						ev.source === "local" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							type: "button",
							onClick: () => remove(ev.id),
							className: "grid size-8 place-items-center text-muted-foreground",
							"aria-label": "Удалить",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" })
						}) : null
					]
				}, ev.id))
			})]
		}, d.key))]
	})] });
}
var SplitComponent = CalendarView;
//#endregion
export { SplitComponent as component };
