import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { l as Rss, r as Trash2, s as Send } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { f as haptic, l as cn, n as Input, s as Button } from "./router-BZC-qIbN.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
import { t as useSources } from "./sources-BZbtlKHk.mjs";
import { n as ServiceRow } from "./service-row-RY8e-WuZ.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/sources-D6zWncel.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function SourcesView() {
	const { sources, add, remove, toggle } = useSources();
	const [type, setType] = (0, import_react.useState)("rss");
	const [name, setName] = (0, import_react.useState)("");
	const [title, setTitle] = (0, import_react.useState)("");
	const submit = () => {
		const err = add({
			type,
			name,
			title: title || name
		});
		if (err) {
			toast(err);
			return;
		}
		setName("");
		setTitle("");
		haptic("medium");
		toast("Источник подключён");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Источники",
		subtitle: "Каналы и RSS для дайджеста",
		backTo: "/digest"
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, { children: sources.map((s, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: i > 0 ? "border-t border-border" : "",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
				icon: s.type === "tg" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Send, { className: "size-5" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Rss, { className: "size-5" }),
				title: s.title,
				status: s.enabled ? s.type === "tg" ? "Telegram · отключён парсер" : "RSS" : "выключен",
				chevron: false,
				onClick: () => toggle(s.id),
				trailing: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					onClick: (e) => {
						e.stopPropagation();
						haptic();
						remove(s.id);
					},
					className: "grid size-9 place-items-center rounded-xl bg-muted text-muted-foreground",
					"aria-label": "Удалить",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "size-4" })
				})
			})
		}, s.id)) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
			className: "space-y-3 p-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex gap-1.5 rounded-xl bg-muted p-1.5",
					children: [{
						id: "rss",
						label: "RSS"
					}, {
						id: "tg",
						label: "Telegram"
					}].map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setType(t.id),
						className: cn("h-10 flex-1 rounded-lg text-xs font-bold", type === t.id ? "bg-accent text-accent-foreground" : "text-muted-foreground"),
						children: t.label
					}, t.id))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
					value: name,
					onChange: (e) => setName(e.target.value),
					placeholder: type === "tg" ? "@channel или t.me/…" : "https://site.com/rss"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
					value: title,
					onChange: (e) => setTitle(e.target.value),
					placeholder: "Название (необязательно)"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					className: "w-full",
					onClick: submit,
					children: "Подключить источник"
				}),
				type === "tg" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs leading-relaxed text-muted-foreground",
					children: "Telegram-каналы зарезервированы в архитектуре. Сейчас дайджест читает HTTPS RSS — укажите ленту издания, если она есть."
				}) : null
			]
		})]
	})] });
}
var SplitComponent = SourcesView;
//#endregion
export { SplitComponent as component };
