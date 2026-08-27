import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as createServerFn } from "./ssr.mjs";
import { n as create, t as persist } from "../_libs/zustand.mjs";
import { r as Trash2, t as X } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { t as useMutation } from "../_libs/tanstack__react-query.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { f as haptic, l as cn, m as uid, n as Input, r as Textarea, s as Button } from "./router-BZC-qIbN.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/translate-COzbgMwF.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var translateText = createServerFn({ method: "POST" }).validator((data) => data).handler(createSsrRpc("942cd3f894f0e29d46c32574b074909ec7cb4fdd9481542258cc4ea51fb3daca"));
var useDictionary = create()(persist((set) => ({
	entries: [],
	add: (src, dst, pair) => {
		const s = src.trim();
		if (!s) return;
		set((st) => ({ entries: [{
			id: uid(),
			src: s.slice(0, 500),
			dst: dst.trim().slice(0, 500),
			pair,
			createdAt: Date.now()
		}, ...st.entries].slice(0, 200) }));
	},
	remove: (id) => set((st) => ({ entries: st.entries.filter((e) => e.id !== id) }))
}), { name: "r2d2.dict.v1" }));
var PAIRS = [
	{
		id: "en|ru",
		label: "EN → RU"
	},
	{
		id: "ru|en",
		label: "RU → EN"
	},
	{
		id: "es|ru",
		label: "ES → RU"
	},
	{
		id: "ru|es",
		label: "RU → ES"
	}
];
function TranslateView() {
	const { entries, add, remove } = useDictionary();
	const [pair, setPair] = (0, import_react.useState)("en|ru");
	const [text, setText] = (0, import_react.useState)("");
	const [result, setResult] = (0, import_react.useState)("");
	const [src, setSrc] = (0, import_react.useState)("");
	const [dst, setDst] = (0, import_react.useState)("");
	const tr = useMutation({
		mutationFn: () => translateText({ data: {
			text,
			pair
		} }),
		onSuccess: (d) => setResult(d.text),
		onError: (e) => toast(e instanceof Error ? e.message : "Ошибка перевода")
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Переводчик",
		subtitle: "Английский, испанский, русский",
		backTo: "/",
		right: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			size: "icon-sm",
			"aria-label": "Очистить",
			onClick: () => {
				setText("");
				setResult("");
			},
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "size-4" })
		})
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, {
				className: "flex gap-1 p-1.5",
				children: PAIRS.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					onClick: () => {
						haptic("light");
						setPair(p.id);
						setResult("");
					},
					className: cn("h-10 flex-1 rounded-xl text-xs font-bold transition-colors duration-150", pair === p.id ? "bg-accent text-accent-foreground" : "text-muted-foreground"),
					children: p.label
				}, p.id))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
						rows: 4,
						value: text,
						onChange: (e) => setText(e.target.value.slice(0, 1500)),
						placeholder: "Вставьте текст для перевода…"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							className: "flex-1",
							disabled: tr.isPending || !text.trim(),
							onClick: () => {
								haptic("medium");
								tr.mutate();
							},
							children: tr.isPending ? "…" : "Перевести"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "secondary",
							size: "icon",
							onClick: () => {
								setText("");
								setResult("");
							},
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" })
						})]
					}),
					result ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2 rounded-xl border border-success/25 bg-success/10 p-3.5",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "whitespace-pre-wrap break-words text-sm",
							children: result
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex gap-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								variant: "ghost",
								size: "sm",
								onClick: () => {
									navigator.clipboard.writeText(result);
									haptic("success");
									toast("Скопировано");
								},
								children: "Копировать"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								size: "sm",
								variant: "solid",
								className: "flex-1",
								onClick: () => {
									add(text, result, pair);
									haptic("medium");
									toast("В словаре");
								},
								children: "В словарь"
							})]
						})]
					}) : null
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
							children: [
								"Словарь (",
								entries.length,
								")"
							]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "text-xs text-muted-foreground",
							children: "на этом устройстве"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						value: src,
						onChange: (e) => setSrc(e.target.value),
						placeholder: "Фраза…"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						value: dst,
						onChange: (e) => setDst(e.target.value),
						placeholder: "Перевод…"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "solid",
						className: "w-full",
						disabled: !src.trim(),
						onClick: () => {
							add(src, dst, pair);
							setSrc("");
							setDst("");
							haptic("medium");
						},
						children: "Добавить в словарь"
					}),
					entries.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "rounded-xl bg-muted px-3 py-4 text-center text-xs text-muted-foreground",
						children: "Словарь пуст. Сохраните перевод или добавьте пару вручную."
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "max-h-72 space-y-2 overflow-y-auto",
						children: entries.map((x) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-xl border border-border bg-muted px-3 py-2.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex items-start justify-between gap-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "text-sm font-bold break-words",
									children: x.src
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
									type: "button",
									onClick: () => {
										haptic("light");
										remove(x.id);
									},
									className: "grid size-8 place-items-center text-muted-foreground",
									"aria-label": "Удалить",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" })
								})]
							}), x.dst ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "text-xs text-muted-foreground",
								children: x.dst
							}) : null]
						}, x.id))
					})
				]
			})
		]
	})] });
}
var SplitComponent = TranslateView;
//#endregion
export { SplitComponent as component };
