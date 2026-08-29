// OpenClaw tool-plugin adapter for bounded plans and acceptance checks.
// State is intentionally in-memory: no prompts, responses, or credentials persist.
const { defineToolPlugin } = require("/usr/lib/node_modules/openclaw/dist/plugin-sdk/tool-plugin.js");
const { randomUUID } = require("crypto");

const MAX_STEPS = 8;
const MAX_RETRIES = 1;
const MAX_PLANS = 100;
const plans = new Map();

function clean(value, max = 500) {
  return String(value || "").trim().slice(0, max);
}

function values(input, max, itemMax) {
  return [...new Set((Array.isArray(input) ? input : [])
    .map((item) => clean(item, itemMax)).filter(Boolean))].slice(0, max);
}

function planTask({ goal, kind = "fast", acceptanceCriteria = [] }) {
  const criteria = values(acceptanceCriteria, 8, 200);
  if (!clean(goal) || !criteria.length) throw new Error("goal and acceptanceCriteria are required");
  if (plans.size >= MAX_PLANS) plans.delete(plans.keys().next().value);
  const id = randomUUID();
  plans.set(id, { id, kind: clean(kind, 32), acceptanceCriteria: criteria,
    completed: [], failed: [], retries: 0 });
  return { ok: true, id, kind: clean(kind, 32), acceptanceCriteria: criteria, next: "continue" };
}

function stepTask({ id, step, ok = true, retry = false }) {
  const plan = plans.get(clean(id, 80));
  if (!plan) throw new Error("unknown plan id");
  if (plan.completed.length + plan.failed.length >= MAX_STEPS) {
    return { ok: false, id: plan.id, next: "ask", reason: "step budget exhausted" };
  }
  if (retry && plan.retries >= MAX_RETRIES) {
    return { ok: false, id: plan.id, next: "continue", reason: "retry budget exhausted" };
  }
  if (retry) plan.retries += 1;
  (ok ? plan.completed : plan.failed).push(clean(step, 300));
  return { ok: true, id: plan.id, stepsUsed: plan.completed.length + plan.failed.length,
    next: ok ? "continue" : (plan.retries < MAX_RETRIES ? "retry" : "continue") };
}

function verifyTask({ id, satisfied = [] }) {
  const plan = plans.get(clean(id, 80));
  if (!plan) throw new Error("unknown plan id");
  const observed = new Set(values(satisfied, 8, 200));
  const missing = plan.acceptanceCriteria.filter((item) => !observed.has(item));
  return { ok: missing.length === 0, id: plan.id, missing, next: missing.length ? "continue" : "finish" };
}

const TOOL_PARAMETERS = {
  type: "object",
  properties: {
    action: { type: "string", enum: ["plan", "step", "verify"] },
    id: { type: "string" },
    goal: { type: "string" },
    kind: { type: "string", enum: ["fast", "research", "coding", "deep", "vision"] },
    acceptanceCriteria: { type: "array", items: { type: "string" } },
    step: { type: "string" },
    ok: { type: "boolean" },
    retry: { type: "boolean" },
    satisfied: { type: "array", items: { type: "string" } },
  },
  required: ["action"],
};

module.exports = defineToolPlugin({
  id: "agent-effectiveness",
  name: "Agent Effectiveness",
  description: "Explicit task plans, bounded retries, and acceptance checks.",
  tools: (tool) => [tool({
    name: "agent_task",
    description: "Plan or verify a task. Actions: plan, step, verify. Use for coding, research, deep analysis, or multi-step automation.",
    parameters: TOOL_PARAMETERS,
    execute: async (params) => {
      if (params.action === "plan") return planTask(params);
      if (params.action === "step") return stepTask(params);
      if (params.action === "verify") return verifyTask(params);
      throw new Error("action must be plan, step, or verify");
    },
  })],
});
