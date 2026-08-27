import { t as createServerFn } from "./ssr.mjs";
import { t as createServerRpc } from "./createServerRpc-A6pJPYTF.mjs";
import { n as fetchJson } from "./cache-DQJ8TyLZ.mjs";
import { r as decodeEntities } from "./sanitize-BO9LSR7k.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/quiz-ifa2tCtd.js
var getQuiz_createServerFn_handler = createServerRpc({
	id: "35006b52e079b8125e37a1269f6c8d91fe778baa53cddafdb6069593d25f4963",
	name: "getQuiz",
	filename: "src/lib/server/quiz.ts"
}, (opts) => getQuiz.__executeServer(opts));
var getQuiz = createServerFn({ method: "GET" }).handler(getQuiz_createServerFn_handler, async () => {
	const row = (await fetchJson("https://opentdb.com/api.php?amount=1&type=multiple", 8e3)).results?.[0];
	if (!row) throw new Error("Нет вопроса");
	return {
		question: decodeEntities(row.question),
		answer: decodeEntities(row.correct_answer),
		category: decodeEntities(row.category),
		difficulty: row.difficulty
	};
});
//#endregion
export { getQuiz_createServerFn_handler };
