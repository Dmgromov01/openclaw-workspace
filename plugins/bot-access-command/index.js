const { execFile } = require("node:child_process");
const { promisify } = require("node:util");
const { definePluginEntry } = require("/usr/lib/node_modules/openclaw/dist/plugin-sdk/plugin-entry.js");
const exec = promisify(execFile);
const OWNER = "1916536646";
const OPERATOR = "/root/openclaw/bin/bot-access-operator";
const ACTIONS = new Map([["status", "status"], ["enable", "enable-restricted"], ["disable", "disable"]]);
module.exports = definePluginEntry({
  id: "bot-access-command", name: "Bot Access Command", description: "Owner-only fixed Telegram access control command",
  register(api) {
    api.registerCommand({
      name: "access", description: "Owner-only: /access status|enable|disable", channels: ["telegram"], acceptsArgs: true,
      requireAuth: true,
      handler: async (ctx) => {
        if (ctx.senderId !== OWNER || ctx.channel !== "telegram") return { text: "Доступ запрещён." };
        const action = ACTIONS.get((ctx.args || "").trim().toLowerCase());
        if (!action) return { text: "Использование: /access status|enable|disable" };
        try {
          const { stdout } = await exec(OPERATOR, [action], { env: { ...process.env, HOME: "/root", OPENCLAW_ACTOR_TG_ID: OWNER }, timeout: 45000, maxBuffer: 131072 });
          const result = JSON.parse(stdout);
          return { text: result.ok ? JSON.stringify(result) : "Операция не выполнена." };
        } catch { return { text: "Операция не выполнена; состояние не изменено." }; }
      },
    });
  },
});
