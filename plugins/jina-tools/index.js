// jina-tools: инструменты Jina AI (Search, RAG via embeddings+rerank)
const { definePluginEntry } = require("/usr/lib/node_modules/openclaw/dist/plugin-sdk/plugin-entry.js");
const { search, rag } = require("./jina-core.js");

module.exports = definePluginEntry({
  id: "jina-tools",
  name: "Jina AI Tools",
  description: "Инструменты Jina AI: jina_search (поиск+контент), jina_rag (semantic search по файлам/памяти)",
  register(api) {
    api.registerTool({
      name: "jina_search",
      description:
        "Поиск в вебе через Jina Search: отдаёт результаты сразу с контентом (markdown). Использовать как резерв, когда web_search даёт слабый результат. Возвращает текст, обрезанный до ~12000 символов.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Поисковый запрос" },
        },
        required: ["query"],
      },
      async execute({ query }) {
        const text = await search(query);
        return { ok: true, result: text };
      },
    });

    api.registerTool({
      name: "jina_rag",
      description:
        "Семантический поиск по файлам/папкам через Jina embeddings + rerank. Важно: выбранные фрагменты передаются внешнему API Jina; инструмент работает только при JINA_RAG_ALLOW_EXTERNAL=1. По умолчанию ищет по памяти (MEMORY.md + memory/*.md), максимум 5 результатов и около 6 КБ результата.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Запрос" },
          paths: {
            type: "array",
            items: { type: "string" },
            description: "Файлы/папки (необязательно; по умолчанию память)",
          },
          topN: { type: "number", description: "Сколько результатов (по умолчанию 5, максимум 5)" },
        },
        required: ["query"],
      },
      async execute({ query, paths, topN }) {
        const r = await rag(query, paths, topN || 5);
        return { ok: true, ...r };
      },
    });
  },
});
