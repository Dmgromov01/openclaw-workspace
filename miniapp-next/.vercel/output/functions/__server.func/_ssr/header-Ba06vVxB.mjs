import { d as useRouterState, v as Link, y as useNavigate } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { E as ArrowLeft, T as Brain, _ as KeyRound, b as Coins, g as Languages, i as SquareCheckBig, o as Settings, p as Newspaper, v as House, w as CalendarDays } from "../_libs/lucide-react.mjs";
import { f as haptic, h as useSettings, l as cn, s as Button } from "./router-BZC-qIbN.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/header-Ba06vVxB.js
var import_jsx_runtime = require_jsx_runtime();
var HUB_MODULES = [
	{
		id: "home",
		title: "Главная",
		shortTitle: "Главная",
		description: "Сводка дня",
		icon: House,
		path: "/",
		showInTabBar: true,
		showOnHome: false,
		order: 0
	},
	{
		id: "digest",
		title: "Дайджест",
		shortTitle: "Дайджест",
		description: "Новости из ваших источников",
		icon: Newspaper,
		path: "/digest",
		showInTabBar: true,
		showOnHome: true,
		order: 1
	},
	{
		id: "fun",
		title: "Викторины и идеи",
		shortTitle: "Викторины",
		description: "Вопросы и занятия",
		icon: Brain,
		path: "/fun",
		showInTabBar: true,
		showOnHome: true,
		order: 2
	},
	{
		id: "translate",
		title: "Переводчик",
		shortTitle: "Перевод",
		description: "Перевод и личный словарь",
		icon: Languages,
		path: "/translate",
		showInTabBar: true,
		showOnHome: true,
		order: 3
	},
	{
		id: "tasks",
		title: "Задачи",
		shortTitle: "Задачи",
		description: "Список дел и архив",
		icon: SquareCheckBig,
		path: "/archive",
		showInTabBar: false,
		showOnHome: true,
		order: 4
	},
	{
		id: "calendar",
		title: "Календарь",
		shortTitle: "Календарь",
		description: "События на 7 дней",
		icon: CalendarDays,
		path: "/calendar",
		showInTabBar: false,
		showOnHome: true,
		order: 5
	},
	{
		id: "rates",
		title: "Валюты",
		shortTitle: "Курсы",
		description: "Курсы ЦБ и конвертер",
		icon: Coins,
		path: "/",
		showInTabBar: false,
		showOnHome: true,
		order: 6
	},
	{
		id: "passwords",
		title: "Пароли",
		shortTitle: "Пароли",
		description: "Генератор надёжных паролей",
		icon: KeyRound,
		path: "/",
		showInTabBar: false,
		showOnHome: true,
		order: 7
	},
	{
		id: "settings",
		title: "Настройки",
		shortTitle: "Ещё",
		description: "Профиль, город, модули",
		icon: Settings,
		path: "/settings",
		showInTabBar: false,
		showOnHome: false,
		order: 8
	}
];
function tabModules(enabled = "all") {
	return HUB_MODULES.filter((m) => m.showInTabBar && (enabled === "all" || enabled.includes(m.id))).sort((a, b) => a.order - b.order);
}
function TabBar() {
	const pathname = useRouterState({ select: (s) => s.location.pathname });
	const tabs = tabModules(useSettings((s) => s.enabledModules));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("nav", {
		className: "tabbar fixed inset-x-0 bottom-0 z-30 flex h-[74px] items-center justify-around border-t border-border bg-card",
		"aria-label": "Основная навигация",
		children: tabs.map((tab) => {
			const active = tab.path === "/" ? pathname === "/" : pathname.startsWith(tab.path);
			const Icon = tab.icon;
			return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
				to: tab.path,
				onClick: () => haptic(),
				className: "flex min-h-11 min-w-14 flex-col items-center justify-center gap-0.5",
				"aria-current": active ? "page" : void 0,
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, {
					className: cn("size-5", active ? "text-accent" : "text-muted-foreground"),
					strokeWidth: active ? 2.2 : 1.8
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: cn("text-[10px] font-medium", active ? "text-accent" : "text-muted-foreground"),
					children: tab.shortTitle
				})]
			}, tab.id);
		})
	});
}
function AppShell({ children, withTabs = true, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: cn("mx-auto min-h-dvh w-full max-w-lg bg-background", withTabs && "pb-[calc(86px+env(safe-area-inset-bottom))]", className),
		children: [children, withTabs ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabBar, {}) : null]
	});
}
function Header({ title, subtitle, backTo, right }) {
	const navigate = useNavigate();
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
		className: "sticky top-0 z-20 flex h-[58px] items-center justify-between gap-2 bg-background px-4",
		style: { paddingTop: "env(safe-area-inset-top)" },
		children: [
			backTo ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				variant: "secondary",
				size: "icon-sm",
				"aria-label": "Назад",
				onClick: () => {
					haptic();
					navigate({ to: backTo });
				},
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowLeft, { className: "size-5" })
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "size-9" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "min-w-0 flex-1 px-2 text-center",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "truncate text-[17px] font-semibold tracking-tight text-foreground",
					children: title
				}), subtitle ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "truncate text-[11px] font-medium text-muted-foreground",
					children: subtitle
				}) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex size-9 items-center justify-center",
				children: right ?? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "size-9" })
			})
		]
	});
}
//#endregion
export { HUB_MODULES as n, Header as r, AppShell as t };
