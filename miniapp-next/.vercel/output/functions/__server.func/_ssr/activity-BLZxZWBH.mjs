import { t as createServerFn } from "./ssr.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
import { n as fetchJson } from "./cache-DQJ8TyLZ.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/activity-BLZxZWBH.js
var getActivity_createServerFn_handler = createServerRpc({
	id: "a3352d9583c6f4fcf11a8b767e95c78c387c8eb0b496e295cf9b4cd8a54f5793",
	name: "getActivity",
	filename: "src/lib/server/activity.ts"
}, (opts) => getActivity.__executeServer(opts));
var getActivity = createServerFn({ method: "GET" }).handler(getActivity_createServerFn_handler, async () => {
	const raw = await fetchJson("https://bored.api.lewagon.com/api/activity", 8e3);
	if (!raw?.activity) throw new Error("Нет идеи");
	return {
		activity: raw.activity,
		type: raw.type,
		participants: raw.participants,
		price: raw.price,
		accessibility: raw.accessibility,
		link: raw.link
	};
});
//#endregion
export { getActivity_createServerFn_handler };
