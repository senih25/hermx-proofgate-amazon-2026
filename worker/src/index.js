// Live demo: a stateless Streamable HTTP MCP endpoint (JSON response mode,
// spec 2025-11-25) plus the static Alexa+ simulator from ../web.
// Each ?sandbox=<id> maps to its own Durable Object, so visitors are isolated.
import { DurableObject } from "cloudflare:workers";
import { ProofGate, ToolError } from "./core.js";

const SERVER_INFO = { name: "HERMX ProofGate · Recall", version: "0.2.0" };
const SUPPORTED = ["2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05"];
const INSTRUCTIONS =
  "Hands-free learning coach with approval-gated effects. Routine reviews (next_review, grade_answer, " +
  "progress) run directly. Importing, resetting or deleting a topic must be planned first, approved with " +
  "the exact spoken approval phrase, executed, then verified. Read each tool's 'say' field aloud.";
const MAX_BODY = 16 * 1024;

const str = (description) => ({ type: "string", description });
const TOOLS = [
  ["proofgate_status", "Service status, safety contract, audit-chain head and state digest.", {}, []],
  ["progress", "Spoken recap of cards, learned cards and cards due, per topic.", {}, []],
  ["next_review", "Next due flashcard (optionally within one topic) to read aloud.", { topic: str("Optional topic slug") }, []],
  ["grade_answer", "Routine effect: grade a spoken answer and reschedule the card (SM-2). Audited, not gated.",
    { card_id: str("Card id from next_review"), answer: str("The learner's spoken answer") }, ["card_id", "answer"]],
  ["plan_change", "Plan a consequential change without executing it. action: import_deck (needs source text), reset_topic, or delete_topic.",
    {
      action: { type: "string", enum: ["import_deck", "reset_topic", "delete_topic"] },
      topic: str('Lowercase slug, e.g. "kubernetes"'),
      source: str("Source text for import_deck"),
      reason: str("Why the change is requested"),
    }, ["action", "topic"]],
  ["approve_change", 'Approve one exact plan with its plan-bound phrase, e.g. "APPROVE 7F3A9C".',
    { plan_id: str("Plan id"), approval_phrase: str("Exact approval phrase") }, ["plan_id", "approval_phrase"]],
  ["execute_change", "Execute an approved plan only if the topic state still matches the plan.", { plan_id: str("Plan id") }, ["plan_id"]],
  ["verify_change", "Verify the result against the approved plan; returns SHA-256 evidence.", { plan_id: str("Plan id") }, ["plan_id"]],
].map(([name, description, properties, required]) => ({
  name, description, inputSchema: { type: "object", properties, required },
}));
const TOOL_NAMES = new Set(TOOLS.map((t) => t.name));

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "content-type, accept, mcp-protocol-version, mcp-session-id",
};
const json = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...CORS } });
const rpcError = (id, code, message) => json({ jsonrpc: "2.0", id: id ?? null, error: { code, message } });

export class Sandbox extends DurableObject {
  async fetch(request) {
    const text = await request.text();
    if (text.length > MAX_BODY) return rpcError(null, -32600, "Request too large");
    let msg;
    try {
      msg = JSON.parse(text);
    } catch {
      return rpcError(null, -32700, "Parse error");
    }
    if (Array.isArray(msg) || msg?.jsonrpc !== "2.0" || typeof msg.method !== "string") {
      return rpcError(msg?.id, -32600, "Invalid Request");
    }
    if (msg.id === undefined) return new Response(null, { status: 202, headers: CORS }); // notification
    const { id, method, params = {} } = msg;

    if (method === "initialize") {
      const asked = params.protocolVersion;
      return json({
        jsonrpc: "2.0", id,
        result: {
          protocolVersion: SUPPORTED.includes(asked) ? asked : SUPPORTED[0],
          capabilities: { tools: { listChanged: false } },
          serverInfo: SERVER_INFO,
          instructions: INSTRUCTIONS,
        },
      });
    }
    if (method === "ping") return json({ jsonrpc: "2.0", id, result: {} });
    if (method === "tools/list") return json({ jsonrpc: "2.0", id, result: { tools: TOOLS } });
    if (method !== "tools/call") return rpcError(id, -32601, `Method not found: ${method}`);

    const { name, arguments: args = {} } = params;
    if (!TOOL_NAMES.has(name)) return rpcError(id, -32602, `Unknown tool: ${name}`);
    const tool = TOOLS.find((t) => t.name === name);
    const missing = tool.inputSchema.required.filter((k) => typeof args[k] !== "string");
    try {
      if (missing.length) throw new ToolError(`INVALID_ARGUMENTS: ${missing.join(", ")}`);
      const result = await new ProofGate(this.ctx.storage)[name](args);
      return json({
        jsonrpc: "2.0", id,
        result: { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result, isError: false },
      });
    } catch (err) {
      if (!(err instanceof ToolError)) throw err;
      return json({
        jsonrpc: "2.0", id,
        result: { content: [{ type: "text", text: `Error executing tool ${name}: ${err.message}` }], isError: true },
      });
    }
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return json({ ok: true, service: "hermx-proofgate-recall", runtime: "cloudflare-worker", version: SERVER_INFO.version });
    }
    if (url.pathname !== "/mcp") return env.ASSETS.fetch(request);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
    if (request.method !== "POST") {
      return new Response("Streamable HTTP endpoint: POST JSON-RPC here. No server-initiated SSE stream.", {
        status: 405, headers: { Allow: "POST", ...CORS },
      });
    }
    const version = request.headers.get("mcp-protocol-version");
    if (version && !SUPPORTED.includes(version)) return rpcError(null, -32600, `Unsupported MCP-Protocol-Version: ${version}`);
    const sandbox = (url.searchParams.get("sandbox") || "public").toLowerCase();
    if (!/^[a-z0-9-]{1,40}$/.test(sandbox)) return rpcError(null, -32600, "Invalid sandbox id");
    return env.SANDBOX.get(env.SANDBOX.idFromName(sandbox)).fetch(request);
  },
};
