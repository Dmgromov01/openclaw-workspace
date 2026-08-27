import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { y as useNavigate } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as createServerFn } from "./ssr.mjs";
import { c as ScanText, d as Radio, l as Rss, u as RefreshCw } from "../_libs/lucide-react.mjs";
import { r as Header, t as AppShell } from "./header-Ba06vVxB.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { n as useQuery, t as useMutation } from "../_libs/tanstack__react-query.mjs";
import { f as haptic, s as Button } from "./router-BZC-qIbN.mjs";
import { t as Card } from "./card-CXjUnk0y.mjs";
import { t as useSources } from "./sources-BZbtlKHk.mjs";
import { n as ServiceRow } from "./service-row-RY8e-WuZ.mjs";
import { t as Skeleton } from "./skeleton-DBbwtrCG.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/digest-CgUhXTCS.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var getDigest = createServerFn({ method: "POST" }).validator((data) => data).handler(createSsrRpc("e5e829d5b7467a7dc6a78e3aa48d8a3faa53e7dee6708408ecbea27398aa55d3"));
var summarizeDigest = createServerFn({ method: "POST" }).validator((data) => data).handler(createSsrRpc("8795c6ca53661950be33beb49cb11eb7ea47c2ff3d44100155972ea4cf15c2a6"));
function DigestView() {
	const navigate = useNavigate();
	const sources = useSources((s) => s.sources.filter((x) => x.enabled));
	const [open, setOpen] = (0, import_react.useState)({});
	const [summaries, setSummaries] = (0, import_react.useState)({});
	const q = useQuery({
		queryKey: ["digest", sources.map((s) => s.id).join(",")],
		queryFn: () => getDigest({ data: { sources: sources.map((s) => ({
			type: s.type,
			name: s.name,
			title: s.title
		})) } })
	});
	const sum = useMutation({
		mutationFn: (i) => {
			const block = q.data?.blocks[i];
			if (!block) return Promise.resolve({ text: "" });
			return summarizeDigest({ data: {
				title: block.title,
				posts: block.posts.map((p) => p.text)
			} });
		},
		onSuccess: (res, i) => {
			if (res.unavailable) {
				setSummaries((s) => ({
					...s,
					[i]: "AI-саммари сейчас недоступно."
				}));
				return;
			}
			if (res.text) setSummaries((s) => ({
				...s,
				[i]: res.text
			}));
		}
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AppShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Header, {
		title: "Дайджест",
		subtitle: `${sources.length} источников`,
		backTo: "/",
		right: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			size: "icon-sm",
			"aria-label": "Обновить",
			onClick: () => {
				haptic("light");
				q.refetch();
			},
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "size-4" })
		})
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 px-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
				icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Radio, { className: "size-5" }),
				title: "Источники",
				status: `${sources.length} подключено · RSS`,
				onClick: () => {
					haptic();
					navigate({ to: "/sources" });
				}
			}) }),
			q.isLoading ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-36" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-36" })]
			}) : null,
			q.isError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "py-8 text-center text-sm text-destructive",
				children: "Не удалось собрать дайджест."
			}) : null,
			q.data?.blocks.map((block, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ServiceRow, {
				icon: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Rss, { className: "size-5" }),
				title: block.title,
				status: block.error ? block.error : `${block.posts.length} материалов`,
				chevron: false
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2.5 border-t border-border px-4 py-3",
				children: [
					summaries[i] ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm leading-relaxed text-foreground",
						children: summaries[i]
					}) : null,
					open[i] ? block.posts.map((p, pi) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "rounded-xl bg-muted px-3 py-2 text-xs leading-relaxed text-muted-foreground",
						children: p.text
					}, pi)) : null,
					block.posts.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "secondary",
							className: "flex-1",
							onClick: () => {
								haptic("light");
								setOpen((s) => ({
									...s,
									[i]: !s[i]
								}));
							},
							children: open[i] ? "Скрыть" : `Показать (${block.posts.length})`
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "outline",
							onClick: () => {
								haptic("medium");
								sum.mutate(i);
							},
							disabled: sum.isPending,
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScanText, { className: "size-4" }), "Саммари"]
						})]
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs text-muted-foreground",
						children: block.error || "Свежих материалов нет."
					})
				]
			})] }, block.title + i)),
			q.data && q.data.blocks.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "py-8 text-center text-sm text-muted-foreground",
				children: "Добавьте источники, чтобы собрать ленту."
			}) : null
		]
	})] });
}
var SplitComponent = DigestView;
//#endregion
export { SplitComponent as component };
