import { n as create, t as persist } from "../_libs/zustand.mjs";
import { m as uid } from "./router-BZC-qIbN.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/tasks-CwEoy1bP.js
var seed = [{
	id: "seed-1",
	text: "Согласовать спецификацию",
	done: false,
	createdAt: Date.now() - 36e5
}, {
	id: "seed-2",
	text: "Проверить выгрузку реестра",
	done: true,
	createdAt: Date.now() - 864e5
}];
var useTasks = create()(persist((set) => ({
	tasks: seed,
	add: (text) => {
		const t = text.trim();
		if (!t) return;
		set((s) => ({ tasks: [{
			id: uid(),
			text: t.slice(0, 240),
			done: false,
			createdAt: Date.now()
		}, ...s.tasks] }));
	},
	toggle: (id) => set((s) => ({ tasks: s.tasks.map((t) => t.id === id ? {
		...t,
		done: !t.done
	} : t) })),
	remove: (id) => set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),
	clearDone: () => set((s) => ({ tasks: s.tasks.filter((t) => !t.done) }))
}), { name: "r2d2.tasks.v1" }));
//#endregion
export { useTasks as t };
