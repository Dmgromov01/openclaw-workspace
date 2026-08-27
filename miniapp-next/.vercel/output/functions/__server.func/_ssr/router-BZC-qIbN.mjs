import { i as __toESM } from "../_runtime.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { _ as createRootRoute, b as useRouter, g as createFileRoute, h as lazyRouteComponent, l as Scripts, m as Outlet, p as createRouter, u as HeadContent } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as Slot } from "../_libs/@radix-ui/react-primitive+[...].mjs";
import { t as createServerFn } from "./ssr.mjs";
import { n as create, t as persist } from "../_libs/zustand.mjs";
import { n as clsx, t as cva } from "../_libs/class-variance-authority+clsx.mjs";
import { t as twMerge } from "../_libs/tailwind-merge.mjs";
import { n as TriangleAlert } from "../_libs/lucide-react.mjs";
import { t as createSsrRpc } from "./createSsrRpc-C1p7zOu_.mjs";
import { r as QueryClientProvider, t as useMutation } from "../_libs/tanstack__react-query.mjs";
import { t as QueryClient } from "../_libs/tanstack__query-core.mjs";
import { t as Toaster } from "../_libs/sonner.mjs";
import { a as union, i as string, n as number, r as object, t as literal } from "../_libs/zod.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/haptic-B18f4qsO.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var MOSCOW = {
	name: "Москва",
	lat: 55.7558,
	lon: 37.6173,
	tz: "Europe/Moscow",
	country: "Россия"
};
var initial = {
	displayName: "",
	onboarded: false,
	theme: "system",
	city: MOSCOW,
	enabledModules: "all",
	pinSalt: null,
	pinHash: null
};
var useSettings = create()(persist((set) => ({
	...initial,
	setDisplayName: (displayName) => set({ displayName }),
	setOnboarded: (onboarded) => set({ onboarded }),
	setTheme: (theme) => set({ theme }),
	setCity: (city) => set({ city }),
	setEnabledModules: (enabledModules) => set({ enabledModules }),
	setPin: (pinSalt, pinHash) => set({
		pinSalt,
		pinHash
	}),
	clearPin: () => set({
		pinSalt: null,
		pinHash: null
	}),
	resetAll: () => set({ ...initial })
}), { name: "r2d2.settings.v1" }));
async function hashPin(pin, saltHex) {
	const enc = new TextEncoder();
	const salt = saltHex ? Uint8Array.from(saltHex.match(/.{2}/g).map((b) => parseInt(b, 16))) : crypto.getRandomValues(/* @__PURE__ */ new Uint8Array(16));
	const key = await crypto.subtle.importKey("raw", enc.encode(pin), "PBKDF2", false, ["deriveBits"]);
	const bits = await crypto.subtle.deriveBits({
		name: "PBKDF2",
		salt,
		iterations: 12e4,
		hash: "SHA-256"
	}, key, 256);
	const hash = [...new Uint8Array(bits)].map((b) => b.toString(16).padStart(2, "0")).join("");
	return {
		salt: [...salt].map((b) => b.toString(16).padStart(2, "0")).join(""),
		hash
	};
}
async function verifyPin(pin, salt, hash) {
	const next = await hashPin(pin, salt);
	if (next.hash.length !== hash.length) return false;
	let diff = 0;
	for (let i = 0; i < hash.length; i++) diff |= next.hash.charCodeAt(i) ^ hash.charCodeAt(i);
	return diff === 0;
}
function cn(...inputs) {
	return twMerge(clsx(inputs));
}
function formatTime(date, locale = "ru-RU") {
	return date.toLocaleTimeString(locale, {
		hour: "2-digit",
		minute: "2-digit"
	});
}
function formatDayLabel(date, locale = "ru-RU") {
	const WEEKDAYS = [
		"вс",
		"пн",
		"вт",
		"ср",
		"чт",
		"пт",
		"сб"
	];
	const MONTHS = [
		"янв",
		"фев",
		"мар",
		"апр",
		"май",
		"июн",
		"июл",
		"авг",
		"сен",
		"окт",
		"ноя",
		"дек"
	];
	const today = /* @__PURE__ */ new Date();
	const isToday = date.getFullYear() === today.getFullYear() && date.getMonth() === today.getMonth() && date.getDate() === today.getDate();
	const label = `${WEEKDAYS[date.getDay()]} ${date.getDate()} ${MONTHS[date.getMonth()]}`;
	return isToday ? `${label} · сегодня` : label;
}
function uid() {
	return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
var buttonVariants = cva("inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-[transform,background-color,opacity,box-shadow] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 disabled:pointer-events-none disabled:opacity-40 active:not-disabled:scale-[0.96] [&_svg]:size-4 [&_svg]:shrink-0", {
	variants: {
		variant: {
			default: "bg-accent text-accent-foreground shadow-sm hover:opacity-90",
			solid: "bg-foreground text-background hover:opacity-90",
			secondary: "bg-muted text-foreground hover:bg-border",
			outline: "border border-border bg-card text-foreground hover:bg-muted",
			ghost: "text-foreground hover:bg-muted",
			destructive: "bg-destructive text-accent-foreground hover:opacity-90"
		},
		size: {
			default: "h-11 px-4",
			sm: "h-9 rounded-lg px-3 text-xs",
			lg: "h-12 px-5",
			icon: "size-11",
			"icon-sm": "size-9 rounded-xl"
		}
	},
	defaultVariants: {
		variant: "default",
		size: "default"
	}
});
function Button({ className, variant, size, asChild = false, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(asChild ? Slot : "button", {
		className: cn(buttonVariants({
			variant,
			size,
			className
		})),
		...props
	});
}
function haptic(kind = "light") {
	try {
		const tg = window.Telegram?.WebApp?.HapticFeedback;
		if (tg) {
			if (kind === "success") tg.notificationOccurred("success");
			else tg.impactOccurred(kind);
			return;
		}
	} catch {}
	if (typeof navigator !== "undefined" && "vibrate" in navigator) {
		const ms = kind === "heavy" ? 24 : kind === "medium" ? 16 : kind === "success" ? 12 : 8;
		navigator.vibrate(ms);
	}
}
//#endregion
//#region node_modules/.nitro/vite/services/ssr/assets/router-BZC-qIbN.js
var __defProp = Object.defineProperty;
var __exportAll = (all, no_symbols) => {
	let target = {};
	for (var name in all) __defProp(target, name, {
		get: all[name],
		enumerable: true
	});
	if (!no_symbols) __defProp(target, Symbol.toStringTag, { value: "Module" });
	return target;
};
function AppErrorComponent({ error }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("main", {
		className: "flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "text-red-500",
				"aria-hidden": "true",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TriangleAlert, {
					className: "size-10",
					strokeWidth: 2
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
				className: "text-lg font-semibold",
				children: "Something went wrong"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "max-w-md text-sm break-words text-zinc-500 dark:text-zinc-400",
				children: error.message || "An unexpected error occurred. Try reloading the page."
			})
		]
	});
}
var queryClient = new QueryClient({ defaultOptions: { queries: {
	staleTime: 6e4,
	retry: 1,
	refetchOnWindowFocus: false
} } });
function applyTheme(theme) {
	const root = document.documentElement;
	const dark = theme === "dark" || theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches;
	root.classList.toggle("dark", dark);
}
function ThemeProvider({ children }) {
	const theme = useSettings((s) => s.theme);
	(0, import_react.useEffect)(() => {
		applyTheme(theme);
		if (theme !== "system") return;
		const mq = window.matchMedia("(prefers-color-scheme: dark)");
		const onChange = () => applyTheme("system");
		mq.addEventListener("change", onChange);
		return () => mq.removeEventListener("change", onChange);
	}, [theme]);
	return children;
}
function AuthProvider({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(QueryClientProvider, {
		client: queryClient,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(ThemeProvider, { children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Toaster, {
			position: "bottom-center",
			toastOptions: { className: "!bg-foreground !text-background !border-none !rounded-xl !text-sm !font-medium" }
		})] })
	});
}
function isGrokEmbedderOrigin(origin) {
	try {
		const url = new URL(origin);
		if (url.protocol !== "https:" && url.protocol !== "http:") return false;
		const host = url.hostname.toLowerCase();
		if (host === "grok.com" || host.endsWith(".grok.com")) return true;
		if (host === "localhost" || host === "127.0.0.1" || host === "[::1]") return true;
		return false;
	} catch {
		return false;
	}
}
function isSandboxPreviewGuestHost(hostname) {
	const host = hostname.toLowerCase();
	return host === "grok-sandbox.com" || host.endsWith(".grok-sandbox.com");
}
function isRemintPreviewPair(guestHost, parentHost) {
	const guest = guestHost.toLowerCase();
	const parent = parentHost.toLowerCase();
	const i = guest.indexOf(".preview.");
	if (i <= 0) return false;
	const label = guest.slice(0, i);
	const rest = guest.slice(i + 9);
	if (label.includes(".") || !rest.includes(".")) return false;
	return parent === rest || parent === `grok.${rest}`;
}
function resolveParentEmbedderOrigin(parentIsSelf, referrer, ancestorOrigin, guestHostname = "") {
	if (parentIsSelf) return null;
	for (const candidate of [referrer, ancestorOrigin ?? ""].filter(Boolean)) try {
		const url = new URL(candidate.includes("://") ? candidate : `https://${candidate}`);
		if (url.protocol !== "https:" && url.protocol !== "http:") continue;
		if (isGrokEmbedderOrigin(url.origin)) return url.origin;
		if (isSandboxPreviewGuestHost(guestHostname) || isRemintPreviewPair(guestHostname, url.hostname)) return url.origin;
	} catch {}
	return null;
}
/**
* Guest side of the grok-web ↔ sandbox preview postMessage bridge.
*
* Activates only when this page is framed by an allowlisted Grok embedder.
* Top-level runs (download/export, local `npm run dev`, deployed sites) noop.
*/
var PREVIEW_BRIDGE_CHANNEL = "grok-preview-bridge";
var EnvelopeSchema = object({
	channel: literal(PREVIEW_BRIDGE_CHANNEL),
	version: number().int().positive(),
	type: string().min(1)
});
var HelloSchema = EnvelopeSchema.extend({ type: literal("hello") });
var NavigateSchema = EnvelopeSchema.extend({
	type: literal("navigate"),
	path: string().min(1)
});
var HistorySchema = EnvelopeSchema.extend({
	type: literal("history"),
	delta: union([literal(-1), literal(1)])
});
function isSafeBridgePath(path) {
	if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\")) return false;
	try {
		return new URL(path, "https://preview.invalid").origin === "https://preview.invalid";
	} catch {
		return false;
	}
}
/**
* Install host↔guest messaging. Returns a dispose function.
* Noops (returns a no-op dispose) when not embedded under a Grok parent.
*/
function installPreviewHostBridge(options = {}) {
	if (typeof window === "undefined") return () => {};
	const ancestorOrigin = typeof location.ancestorOrigins !== "undefined" && location.ancestorOrigins.length > 0 ? location.ancestorOrigins[0] : null;
	const parentOrigin = resolveParentEmbedderOrigin(window.parent === window, document.referrer, ancestorOrigin, window.location.hostname);
	if (parentOrigin === null) return () => {};
	const ROOT_STATE_KEY = "__grokPreviewBridgeRoot";
	const originalPushState = window.history.pushState.bind(window.history);
	const originalReplaceState = window.history.replaceState.bind(window.history);
	const isAtHistoryRoot = () => {
		const state = window.history.state;
		return Boolean(state && typeof state === "object" && state[ROOT_STATE_KEY] === true);
	};
	try {
		const current = window.history.state;
		if (!(current !== null && typeof current === "object" && Object.prototype.hasOwnProperty.call(current, ROOT_STATE_KEY))) {
			const isRoot = window.history.length <= 1;
			originalReplaceState(current && typeof current === "object" ? {
				...current,
				[ROOT_STATE_KEY]: isRoot
			} : { [ROOT_STATE_KEY]: isRoot }, "", window.location.href);
		}
	} catch {}
	const post = (message) => {
		window.parent.postMessage(message, parentOrigin);
	};
	const reportLocation = () => {
		post({
			channel: PREVIEW_BRIDGE_CHANNEL,
			version: 1,
			type: "location",
			path: window.location.pathname || "/",
			search: window.location.search,
			hash: window.location.hash
		});
	};
	const reportRoutes = () => {
		const paths = options.getRoutePaths?.() ?? [];
		post({
			channel: PREVIEW_BRIDGE_CHANNEL,
			version: 1,
			type: "routes",
			paths
		});
	};
	const defaultNavigate = (path) => {
		if (!isSafeBridgePath(path)) return;
		try {
			const url = new URL(path, window.location.origin);
			if (url.origin !== window.location.origin) return;
			const next = `${url.pathname}${url.search}${url.hash}`;
			window.history.pushState(window.history.state, "", next);
			window.dispatchEvent(new PopStateEvent("popstate", { state: window.history.state }));
		} catch {}
	};
	const navigate = (path) => {
		if (!isSafeBridgePath(path)) return;
		if (options.navigate) {
			options.navigate(path);
			return;
		}
		defaultNavigate(path);
	};
	const announce = () => {
		reportLocation();
		reportRoutes();
		post({
			channel: PREVIEW_BRIDGE_CHANNEL,
			version: 1,
			type: "ready"
		});
	};
	const onMessage = (event) => {
		if (event.source !== window.parent) return;
		if (event.origin !== parentOrigin) return;
		const envelope = EnvelopeSchema.safeParse(event.data);
		if (!envelope.success || envelope.data.version !== 1) return;
		if (envelope.data.type === "hello") {
			if (!HelloSchema.safeParse(event.data).success) return;
			announce();
			return;
		}
		if (envelope.data.type === "navigate") {
			const parsed = NavigateSchema.safeParse(event.data);
			if (!parsed.success) return;
			navigate(parsed.data.path);
			queueMicrotask(reportLocation);
			return;
		}
		if (envelope.data.type === "history") {
			const parsed = HistorySchema.safeParse(event.data);
			if (!parsed.success) return;
			if (parsed.data.delta === -1 && isAtHistoryRoot()) return;
			window.history.go(parsed.data.delta);
		}
	};
	const onPopState = () => {
		reportLocation();
	};
	const onHashChange = () => {
		reportLocation();
	};
	window.history.pushState = (data, unused, url) => {
		const next = data && typeof data === "object" ? {
			...data,
			[ROOT_STATE_KEY]: false
		} : data;
		originalPushState(next, unused, url);
		reportLocation();
	};
	window.history.replaceState = (data, unused, url) => {
		const next = isAtHistoryRoot() ? {
			...data && typeof data === "object" ? data : {},
			[ROOT_STATE_KEY]: true
		} : data;
		originalReplaceState(next, unused, url);
		reportLocation();
	};
	window.addEventListener("message", onMessage);
	window.addEventListener("popstate", onPopState);
	window.addEventListener("hashchange", onHashChange);
	announce();
	return () => {
		window.removeEventListener("message", onMessage);
		window.removeEventListener("popstate", onPopState);
		window.removeEventListener("hashchange", onHashChange);
		window.history.pushState = originalPushState;
		window.history.replaceState = originalReplaceState;
	};
}
/** Collect static path patterns from a TanStack route tree (best-effort). */
function collectRoutePathsFromTree(routeTree) {
	const paths = /* @__PURE__ */ new Set();
	const walk = (node) => {
		if (!node || typeof node !== "object") return;
		const record = node;
		const full = typeof record.fullPath === "string" ? record.fullPath : typeof record.path === "string" ? record.path : null;
		if (full !== null && full !== "") paths.add(full.startsWith("/") ? full : `/${full}`);
		else if (full === "") paths.add("/");
		const children = record.children;
		if (Array.isArray(children)) for (const child of children) walk(child);
		else if (children && typeof children === "object") for (const child of Object.values(children)) walk(child);
	};
	walk(routeTree);
	return [...paths];
}
/**
* Mount once in `__root.tsx` so the Grok preview chrome can drive navigation
* (and later receive registered routes). Noops when the app is not embedded.
*/
function PreviewHostBridge() {
	const router = useRouter();
	(0, import_react.useEffect)(() => {
		return installPreviewHostBridge({
			navigate: (path) => {
				router.history.push(path);
			},
			getRoutePaths: () => collectRoutePathsFromTree(router.routeTree)
		});
	}, [router]);
	return null;
}
var KEY = "r2d2.unlocked";
function isSessionUnlocked() {
	if (typeof window === "undefined") return true;
	return sessionStorage.getItem(KEY) === "1";
}
function unlockSession() {
	sessionStorage.setItem(KEY, "1");
}
function lockSession() {
	sessionStorage.removeItem(KEY);
}
var getWeather = createServerFn({ method: "GET" }).validator((data) => data).handler(createSsrRpc("7cf7d5e69bcb3ccff5d1b5139f463568a2ca48ece792ed1d28515bda49861864"));
var searchCities = createServerFn({ method: "GET" }).validator((data) => data).handler(createSsrRpc("828bedc192e156c67e34471d374a4df5027fff3e4f3d0156db94b97d15318830"));
function Input({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
		className: cn("flex h-11 w-full rounded-xl border border-border bg-muted px-3.5 text-sm text-foreground outline-none transition-[box-shadow,border-color] duration-150 placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/50", className),
		...props
	});
}
function Textarea({ className, ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
		className: cn("flex min-h-24 w-full resize-none rounded-xl border border-border bg-muted p-3.5 text-sm text-foreground outline-none transition-[box-shadow,border-color] duration-150 placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring/50", className),
		...props
	});
}
function Onboarding() {
	const setDisplayName = useSettings((s) => s.setDisplayName);
	const setCity = useSettings((s) => s.setCity);
	const setOnboarded = useSettings((s) => s.setOnboarded);
	const [name, setName] = (0, import_react.useState)("");
	const [query, setQuery] = (0, import_react.useState)("Москва");
	const [city, setLocalCity] = (0, import_react.useState)(MOSCOW);
	const search = useMutation({ mutationFn: (q) => searchCities({ data: { q } }) });
	const finish = () => {
		const n = name.trim().slice(0, 40) || "Гость";
		setDisplayName(n);
		setCity(city);
		setOnboarded(true);
		haptic("success");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6 py-10",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "enter",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground",
						children: "Personal hub"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
						className: "mt-2 text-4xl font-semibold tracking-tight text-foreground",
						children: "R2D2"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground",
						children: "Погода, курсы, задачи, дайджест и переводчик — в одном спокойном экране."
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "enter enter-2 mt-8 space-y-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "block text-xs font-semibold text-muted-foreground",
						children: "Как к вам обращаться"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						value: name,
						onChange: (e) => setName(e.target.value),
						placeholder: "Имя",
						autoFocus: true
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "block pt-2 text-xs font-semibold text-muted-foreground",
						children: "Город для погоды"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							value: query,
							onChange: (e) => setQuery(e.target.value),
							onKeyDown: (e) => {
								if (e.key === "Enter") search.mutate(query);
							},
							placeholder: "Найти город"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "button",
							variant: "secondary",
							onClick: () => search.mutate(query),
							children: "Найти"
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
							type: "button",
							onClick: () => {
								setLocalCity(MOSCOW);
								setQuery(MOSCOW.name);
							},
							className: "w-full rounded-xl border border-border bg-card px-3 py-2.5 text-left text-sm font-medium",
							children: [city.name === MOSCOW.name ? "Выбрано: " : "", "Москва"]
						}), (search.data ?? []).map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
							type: "button",
							onClick: () => {
								setLocalCity({
									name: c.name,
									lat: c.lat,
									lon: c.lon,
									tz: c.tz,
									country: c.country
								});
								setQuery(c.name);
							},
							className: "w-full rounded-xl border border-border bg-muted px-3 py-2.5 text-left text-sm",
							children: [
								c.name,
								c.admin ? `, ${c.admin}` : "",
								c.country ? ` · ${c.country}` : ""
							]
						}, `${c.lat}-${c.lon}`))]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				className: "enter enter-3 mt-8 h-12 w-full",
				onClick: finish,
				children: "Продолжить"
			})
		]
	});
}
function LockScreen({ onUnlock }) {
	const pinSalt = useSettings((s) => s.pinSalt);
	const pinHash = useSettings((s) => s.pinHash);
	const name = useSettings((s) => s.displayName);
	const [pin, setPin] = (0, import_react.useState)("");
	const [err, setErr] = (0, import_react.useState)("");
	const [busy, setBusy] = (0, import_react.useState)(false);
	const submit = async () => {
		if (!pinSalt || !pinHash) {
			onUnlock();
			return;
		}
		setBusy(true);
		setErr("");
		const ok = await verifyPin(pin, pinSalt, pinHash);
		setBusy(false);
		if (!ok) {
			haptic("heavy");
			setErr("Неверный код");
			setPin("");
			return;
		}
		unlockSession();
		haptic("success");
		onUnlock();
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground",
				children: "R2D2"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h1", {
				className: "mt-2 text-3xl font-semibold tracking-tight",
				children: ["Здравствуйте", name ? `, ${name}` : ""]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mt-2 text-sm text-muted-foreground",
				children: "Введите код доступа к хабу."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "mt-8 space-y-3",
				onSubmit: (e) => {
					e.preventDefault();
					submit();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
						type: "password",
						inputMode: "numeric",
						autoComplete: "off",
						value: pin,
						onChange: (e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 8)),
						placeholder: "Код",
						autoFocus: true
					}),
					err ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm font-medium text-destructive",
						children: err
					}) : null,
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						className: "h-12 w-full",
						disabled: busy || pin.length < 4,
						children: "Открыть"
					})
				]
			})
		]
	});
}
function Gate({ children }) {
	const onboarded = useSettings((s) => s.onboarded);
	const pinHash = useSettings((s) => s.pinHash);
	const [unlocked, setUnlocked] = (0, import_react.useState)(true);
	const [ready, setReady] = (0, import_react.useState)(false);
	(0, import_react.useEffect)(() => {
		const finish = () => {
			const hash = useSettings.getState().pinHash;
			setUnlocked(!hash || isSessionUnlocked());
			setReady(true);
		};
		if (useSettings.persist.hasHydrated()) finish();
		return useSettings.persist.onFinishHydration(finish);
	}, [pinHash]);
	if (!ready) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "min-h-dvh bg-background" });
	if (!onboarded) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Onboarding, {});
	if (pinHash && !unlocked) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LockScreen, { onUnlock: () => setUnlocked(true) });
	return children;
}
var styles_default = "/assets/styles-vAVvAkW1.css";
var APP_NAME = "R2D2";
var Route$8 = createRootRoute({
	head: () => ({
		meta: [
			{ charSet: "utf-8" },
			{
				name: "viewport",
				content: "width=device-width, initial-scale=1, viewport-fit=cover"
			},
			{ title: APP_NAME },
			{
				name: "theme-color",
				content: "#F7F8FA"
			},
			{
				name: "description",
				content: "Личный хаб: погода, курсы, задачи, дайджест и переводчик."
			}
		],
		links: [
			{
				rel: "icon",
				type: "image/svg+xml",
				href: "/favicon.svg"
			},
			{
				rel: "stylesheet",
				href: styles_default
			},
			{
				rel: "manifest",
				href: "/__grok/manifest.webmanifest"
			},
			{
				rel: "apple-touch-icon",
				href: "/__grok/icon-180.png"
			},
			{
				rel: "preconnect",
				href: "https://fonts.googleapis.com"
			},
			{
				rel: "preconnect",
				href: "https://fonts.gstatic.com",
				crossOrigin: "anonymous"
			},
			{
				rel: "stylesheet",
				href: "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap"
			}
		]
	}),
	component: RootDocument
});
function RootDocument() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("html", {
		lang: "ru",
		suppressHydrationWarning: true,
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("head", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(HeadContent, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("body", {
			className: "antialiased",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PreviewHostBridge, {}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AuthProvider, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Gate, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Outlet, {}) }) }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Scripts, {})
			]
		})]
	});
}
var $$splitComponentImporter$7 = () => import("./routes-IF4IVczN.mjs");
var Route$7 = createFileRoute("/")({ component: lazyRouteComponent($$splitComponentImporter$7, "component") });
var $$splitComponentImporter$6 = () => import("./archive-J_oDHJAZ.mjs");
var Route$6 = createFileRoute("/archive")({ component: lazyRouteComponent($$splitComponentImporter$6, "component") });
var $$splitComponentImporter$5 = () => import("./calendar-DqYkezF6.mjs");
var Route$5 = createFileRoute("/calendar")({ component: lazyRouteComponent($$splitComponentImporter$5, "component") });
var $$splitComponentImporter$4 = () => import("./digest-CgUhXTCS.mjs");
var Route$4 = createFileRoute("/digest")({ component: lazyRouteComponent($$splitComponentImporter$4, "component") });
var $$splitComponentImporter$3 = () => import("./fun-Ce3x6NXG.mjs");
var Route$3 = createFileRoute("/fun")({ component: lazyRouteComponent($$splitComponentImporter$3, "component") });
var $$splitComponentImporter$2 = () => import("./settings-D6qiVOc6.mjs");
var Route$2 = createFileRoute("/settings")({ component: lazyRouteComponent($$splitComponentImporter$2, "component") });
var $$splitComponentImporter$1 = () => import("./sources-D6zWncel.mjs");
var Route$1 = createFileRoute("/sources")({ component: lazyRouteComponent($$splitComponentImporter$1, "component") });
var $$splitComponentImporter = () => import("./translate-COzbgMwF.mjs");
var Route = createFileRoute("/translate")({ component: lazyRouteComponent($$splitComponentImporter, "component") });
var rootRouteChildren = {
	IndexRoute: Route$7.update({
		id: "/",
		path: "/",
		getParentRoute: () => Route$8
	}),
	ArchiveRoute: Route$6.update({
		id: "/archive",
		path: "/archive",
		getParentRoute: () => Route$8
	}),
	CalendarRoute: Route$5.update({
		id: "/calendar",
		path: "/calendar",
		getParentRoute: () => Route$8
	}),
	DigestRoute: Route$4.update({
		id: "/digest",
		path: "/digest",
		getParentRoute: () => Route$8
	}),
	FunRoute: Route$3.update({
		id: "/fun",
		path: "/fun",
		getParentRoute: () => Route$8
	}),
	SettingsRoute: Route$2.update({
		id: "/settings",
		path: "/settings",
		getParentRoute: () => Route$8
	}),
	SourcesRoute: Route$1.update({
		id: "/sources",
		path: "/sources",
		getParentRoute: () => Route$8
	}),
	TranslateRoute: Route.update({
		id: "/translate",
		path: "/translate",
		getParentRoute: () => Route$8
	})
};
var routeTree = Route$8._addFileChildren(rootRouteChildren)._addFileTypes();
var router_exports = /* @__PURE__ */ __exportAll({ getRouter: () => getRouter });
function getRouter() {
	return createRouter({
		routeTree,
		defaultErrorComponent: AppErrorComponent
	});
}
//#endregion
export { searchCities as a, MOSCOW as c, formatTime as d, haptic as f, useSettings as h, getWeather as i, cn as l, uid as m, Input as n, lockSession as o, hashPin as p, Textarea as r, Button as s, router_exports as t, formatDayLabel as u };
