import { t as createServerFn } from "./ssr.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
import { n as fetchJson, t as cached } from "./cache-DQJ8TyLZ.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/rates-BjPK9nEr.js
var getRates_createServerFn_handler = createServerRpc({
	id: "bf54b31396212cca2300d4310fc752265d3eaaf9c42f3d6e1c78506490e2e2bf",
	name: "getRates",
	filename: "src/lib/server/rates.ts"
}, (opts) => getRates.__executeServer(opts));
var getRates = createServerFn({ method: "GET" }).handler(getRates_createServerFn_handler, async () => {
	return cached("cbr-rates", 18e5, async () => {
		const v = (await fetchJson("https://www.cbr-xml-daily.ru/daily_json.js", 8e3)).Valute ?? {};
		const pick = (code) => {
			const row = v[code];
			if (!row) return 0;
			return row.Value / (row.Nominal || 1);
		};
		return {
			rates: {
				USD: pick("USD"),
				EUR: pick("EUR"),
				CNY: pick("CNY"),
				JPY: pick("JPY"),
				GBP: pick("GBP"),
				RUB: 1
			},
			ts: Date.now()
		};
	});
});
//#endregion
export { getRates_createServerFn_handler };
