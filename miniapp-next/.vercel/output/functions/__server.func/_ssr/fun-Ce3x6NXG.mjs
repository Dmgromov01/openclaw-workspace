import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as createServerFn } from "./ssr.mjs";
import { T as Brain, a as Shuffle, h as Lightbulb } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { n as useQuery } from "../_libs/tanstack__react-query.mjs";
import { f as haptic, l as cn, s as Button } from "./router-BZC-qIbN.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
import { n as ServiceRow } from "./service-row-RY8e-WuZ.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/fun-Ce3x6NXG.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var getQuiz = createServerFn({ method: "GET" }).handler(createSsrRpc("35006b52e079b8125e37a1269f6c8d91fe778baa53cddafdb6069593d25f4963"));
var getActivity = createServerFn({ method: "GET" }).handler(createSsrRpc("a3352d9583c6f4fcf11a8b767e95c78c387c8eb0b496e295cf9b4cd8a54f5793"));
function Badge({ className, tone = "muted", children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
		className: cn("inline-flex items-center rounded-lg px-2 py-0.5 text-xs font-semibold", tone === "muted" && "bg-muted text-muted-foreground", tone === "accent" && "bg-accent-soft text-accent", tone === "success" && "bg-success/10 text-success", tone === "warning" && "bg-warning/15 text-warning", className),
		children
	});
}
function priceLabel(p) {
	if (p == null) return "";
	if (p === 0) return "бесплатно";
	if (p < .3) return "недорого";
	return "платно";
}
function FunView() {
	const [reveal, setReveal] = (0, import_react.useState)(false);
	const quiz = useQuery({
		queryKey: ["quiz"],
		queryFn: () => getQuiz()
	});
	const activity = useQuery({
		queryKey: ["activity"],
		queryFn: () => getActivity()
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Викторины и идеи",
		subtitle: "Вопросы и занятия",
		backTo: "/",
		right: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			size: "icon-sm",
			"aria-label": "Новый вопрос",
			onClick: () => {
				haptic("light");
				setReveal(false);
				quiz.refetch();
			},
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shuffle, { className: "size-4" })
		})
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
			accent: true,
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Brain, { className: "size-5" }),
			title: "Вопрос для викторины",
			status: "Open Trivia DB",
			chevron: false,
			trailing: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				size: "sm",
				onClick: () => {
					haptic("light");
					setReveal(false);
					quiz.refetch();
				},
				disabled: quiz.isFetching,
				children: quiz.isFetching ? "…" : "Новый"
			})
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "space-y-3 border-t border-border px-4 py-3",
			children: [quiz.isError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-destructive",
				children: "Не удалось загрузить вопрос."
			}) : null, quiz.data ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex flex-wrap gap-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: "accent",
						children: quiz.data.category
					}), quiz.data.difficulty ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, { children: quiz.data.difficulty }) : null]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm font-semibold leading-snug",
					children: quiz.data.question
				}),
				!reveal ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "solid",
					className: "w-full",
					onClick: () => {
						haptic("medium");
						setReveal(true);
					},
					children: "Показать ответ"
				}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-xl border border-success/25 bg-success/10 p-3.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-xs font-bold uppercase tracking-wide text-success",
						children: "Ответ"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "text-sm font-semibold",
						children: quiz.data.answer
					})]
				})
			] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "py-6 text-center text-xs text-muted-foreground",
				children: "Загружаем вопрос…"
			})]
		})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
			icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Lightbulb, { className: "size-5" }),
			title: "Чем заняться",
			status: "Bored API",
			chevron: false,
			trailing: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				variant: "solid",
				size: "sm",
				onClick: () => {
					haptic("light");
					activity.refetch();
				},
				disabled: activity.isFetching,
				children: activity.isFetching ? "…" : "Идея"
			})
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "space-y-3 border-t border-border px-4 py-3",
			children: [activity.isError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-destructive",
				children: "Не удалось подобрать занятие."
			}) : null, activity.data ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm font-semibold leading-snug",
				children: activity.data.activity
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap gap-1.5",
				children: [
					activity.data.type ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: "accent",
						children: activity.data.type
					}) : null,
					activity.data.participants ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, { children: [
						activity.data.participants,
						" ",
						activity.data.participants === 1 ? "участник" : "участника"
					] }) : null,
					priceLabel(activity.data.price) ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: "success",
						children: priceLabel(activity.data.price)
					}) : null
				]
			})] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "py-6 text-center text-xs text-muted-foreground",
				children: "Подбираем занятие…"
			})]
		})] })]
	})] });
}
var SplitComponent = FunView;
//#endregion
export { SplitComponent as component };
