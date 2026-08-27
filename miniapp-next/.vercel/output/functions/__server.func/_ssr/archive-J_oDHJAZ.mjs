import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as useTasks } from "./tasks-CwEoy1bP.mjs";
import { r as Trash2, t as X } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { f as haptic, s as Button } from "./router-BZC-qIbN.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/archive-J_oDHJAZ.js
var import_jsx_runtime = require_jsx_runtime();
function ArchiveView() {
	const { tasks, toggle, remove, clearDone } = useTasks();
	const done = tasks.filter((t) => t.done);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Архив дел",
		subtitle: "Выполненные задачи",
		backTo: "/",
		right: done.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			size: "icon-sm",
			"aria-label": "Очистить архив",
			onClick: () => {
				haptic("heavy");
				clearDone();
			},
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "size-4" })
		}) : void 0
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-2.5 px-4",
		children: [done.map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex items-center justify-between gap-2 rounded-xl border border-border bg-card p-3.5",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
				type: "button",
				className: "flex min-w-0 flex-1 items-center gap-3 text-left",
				onClick: () => {
					haptic();
					toggle(t.id);
				},
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid size-6 shrink-0 place-items-center rounded-lg bg-success text-xs font-bold text-accent-foreground",
					children: "✓"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "truncate text-sm font-semibold text-muted-foreground line-through",
					children: t.text
				})]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
				type: "button",
				onClick: () => remove(t.id),
				className: "grid size-9 place-items-center text-muted-foreground hover:text-destructive",
				"aria-label": "Удалить",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" })
			})]
		}, t.id)), done.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "rounded-xl border border-border bg-card px-6 py-10 text-center text-sm text-muted-foreground",
			children: "В архиве нет выполненных задач."
		}) : null]
	})] });
}
var SplitComponent = ArchiveView;
//#endregion
export { SplitComponent as component };
