import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as HUB_MODULES, r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { t as useMutation } from "../_libs/tanstack__react-query.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { a as searchCities, c as MOSCOW, f as haptic, h as useSettings, l as cn, n as Input, o as lockSession, p as hashPin, s as Button } from "./router-BZC-qIbN.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
import { n as SwitchThumb, t as Switch$1 } from "../_libs/@radix-ui/react-switch+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/settings-D6qiVOc6.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function Switch({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch$1, {
		className: cn("peer inline-flex h-7 w-11 shrink-0 items-center rounded-full border border-transparent bg-border transition-colors duration-150 data-[state=checked]:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50", className),
		...props,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SwitchThumb, { className: "pointer-events-none block size-5 translate-x-0.5 rounded-full bg-card shadow-sm transition-transform duration-150 data-[state=checked]:translate-x-[22px]" })
	});
}
function SettingsView() {
	const s = useSettings();
	const [name, setName] = (0, import_react.useState)(s.displayName);
	const [q, setQ] = (0, import_react.useState)(s.city.name);
	const [pin, setPin] = (0, import_react.useState)("");
	const search = useMutation({ mutationFn: (query) => searchCities({ data: { q: query } }) });
	const saveName = () => {
		s.setDisplayName(name.trim().slice(0, 40) || "Гость");
		haptic("success");
		toast("Имя сохранено");
	};
	const setTheme = (theme) => {
		s.setTheme(theme);
		haptic();
	};
	const toggleModule = (id) => {
		const current = s.enabledModules === "all" ? HUB_MODULES.map((m) => m.id) : [...s.enabledModules];
		const next = current.includes(id) ? current.filter((x) => x !== id) : [...current, id];
		const merged = Array.from(/* @__PURE__ */ new Set([...["home", "settings"], ...next]));
		s.setEnabledModules(merged.length >= HUB_MODULES.length ? "all" : merged);
		haptic();
	};
	const enabled = (id) => s.enabledModules === "all" || s.enabledModules.includes(id);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Настройки",
		subtitle: "Профиль и модули",
		backTo: "/"
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
						children: "Профиль"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						value: name,
						onChange: (e) => setName(e.target.value),
						placeholder: "Имя"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "secondary",
						onClick: saveName,
						children: "Сохранить имя"
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
					children: "Тема"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid grid-cols-3 gap-1.5 rounded-xl bg-muted p-1.5",
					children: [
						"light",
						"dark",
						"system"
					].map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setTheme(t),
						className: `h-10 rounded-lg text-xs font-bold ${s.theme === t ? "bg-accent text-accent-foreground" : "text-muted-foreground"}`,
						children: t === "light" ? "Светлая" : t === "dark" ? "Тёмная" : "Система"
					}, t))
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
						children: "Город"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							value: q,
							onChange: (e) => setQ(e.target.value),
							placeholder: "Найти город"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "secondary",
							onClick: () => search.mutate(q),
							children: "Найти"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "text-sm text-muted-foreground",
						children: ["Сейчас: ", s.city.name]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						className: "w-full rounded-xl bg-muted px-3 py-2 text-left text-sm",
						onClick: () => {
							s.setCity(MOSCOW);
							setQ(MOSCOW.name);
						},
						children: "Москва"
					}),
					(search.data ?? []).map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
						type: "button",
						className: "w-full rounded-xl bg-muted px-3 py-2 text-left text-sm",
						onClick: () => {
							s.setCity({
								name: c.name,
								lat: c.lat,
								lon: c.lon,
								tz: c.tz,
								country: c.country
							});
							setQ(c.name);
							toast("Город обновлён");
						},
						children: [c.name, c.admin ? `, ${c.admin}` : ""]
					}, `${c.lat}-${c.lon}`))
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-3 p-4",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-xs font-bold uppercase tracking-wide text-muted-foreground",
						children: "Код доступа"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm text-muted-foreground",
						children: "Локальный PIN на этом устройстве. Не уходит на сервер."
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						type: "password",
						inputMode: "numeric",
						value: pin,
						onChange: (e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 8)),
						placeholder: "4–8 цифр"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							className: "flex-1",
							disabled: pin.length < 4,
							onClick: async () => {
								const { salt, hash } = await hashPin(pin);
								s.setPin(salt, hash);
								setPin("");
								toast("Код установлен");
							},
							children: "Установить"
						}), s.pinHash ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "outline",
							onClick: () => {
								s.clearPin();
								toast("Код снят");
							},
							children: "Снять"
						}) : null]
					}),
					s.pinHash ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "secondary",
						onClick: () => {
							lockSession();
							window.location.reload();
						},
						children: "Заблокировать сейчас"
					}) : null
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-1 p-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground",
					children: "Модули"
				}), HUB_MODULES.filter((m) => m.id !== "home" && m.id !== "settings").map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between gap-3 py-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-sm font-semibold",
						children: m.title
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-xs text-muted-foreground",
						children: m.description
					})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
						checked: enabled(m.id),
						onCheckedChange: () => toggleModule(m.id)
					})]
				}, m.id))]
			})
		]
	})] });
}
var SplitComponent = SettingsView;
//#endregion
export { SplitComponent as component };
