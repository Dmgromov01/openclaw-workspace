import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { x as ChevronRight } from "../_libs/lucide-react.mjs";
import { l as cn } from "./router-BZC-qIbN.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/service-row-RY8e-WuZ.js
var import_jsx_runtime = require_jsx_runtime();
function IconWell({ children, accent = false, className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: cn("flex size-10 shrink-0 items-center justify-center rounded-full border", accent ? "border-transparent bg-accent-soft text-accent" : "border-border bg-muted text-foreground", className),
		children
	});
}
function ServiceRow({ icon, title, status, onClick, trailing, accent, chevron = true }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(onClick ? "button" : "div", {
		type: onClick ? "button" : void 0,
		onClick,
		className: cn("relative flex min-h-16 w-full items-center gap-3 px-3.5 py-2 text-left", onClick && "transition-colors duration-150 hover:bg-muted/60"),
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(IconWell, {
				accent,
				children: icon
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "min-w-0 flex-1",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "truncate text-[15px] font-semibold leading-snug text-foreground",
					children: title
				}), status ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-0.5 truncate text-xs font-medium text-muted-foreground",
					children: status
				}) : null]
			}),
			trailing,
			chevron && onClick ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronRight, { className: "size-4 shrink-0 text-muted-foreground" }) : null
		]
	});
}
//#endregion
export { ServiceRow as n, IconWell as t };
