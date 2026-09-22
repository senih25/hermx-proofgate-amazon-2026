// Port of proofgate_core.py on Durable Object storage (one object per sandbox).
import { grade, makeCards, sha256Hex, BLANK } from "./learning.js";
import { review } from "./srs.js";

export const GATED_ACTIONS = ["import_deck", "reset_topic", "delete_topic"];
export const ROUTINE_TOOLS = ["next_review", "grade_answer", "progress"];
const TOPIC_RE = /^[a-z0-9][a-z0-9-]{0,31}$/;
const MAX_SOURCE_CHARS = 4000;
const MAX_CARDS_PER_IMPORT = 8;
const MAX_TOTAL_CARDS = 200;
const MAX_PLANS = 100; // public demo: keep per-sandbox storage bounded
const GENESIS = "0".repeat(64);

export class ToolError extends Error {}
const fail = (code) => {
  throw new ToolError(code);
};

function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    return "{" + Object.keys(value).sort().map((k) => JSON.stringify(k) + ":" + canonical(value[k])).join(",") + "}";
  }
  return JSON.stringify(value ?? null);
}
const digest = (v) => sha256Hex(canonical(v));
const today = () => new Date().toISOString().slice(0, 10);
const now = () => new Date().toISOString();

const topicSlice = (state, topic) =>
  Object.fromEntries(Object.entries(state.cards).filter(([, c]) => c.topic === topic));

function applyPlan(state, plan) {
  const next = structuredClone(state);
  const fresh = { repetitions: 0, interval_days: 0, easiness: 2.5, due: plan.effective_date };
  if (plan.action === "import_deck") {
    for (const c of plan.payload.cards) {
      next.cards[c.id] = { id: c.id, topic: plan.topic, front: c.front, back: c.back, ...fresh };
    }
  } else if (plan.action === "reset_topic") {
    for (const id of Object.keys(topicSlice(next, plan.topic))) Object.assign(next.cards[id], fresh);
  } else if (plan.action === "delete_topic") {
    for (const id of Object.keys(topicSlice(next, plan.topic))) delete next.cards[id];
  }
  return next;
}

export class ProofGate {
  constructor(storage) {
    this.storage = storage;
  }

  async load() {
    const got = await this.storage.get(["state", "plans", "audit"]);
    return {
      state: got.get("state") ?? { cards: {}, last_change: null },
      plans: got.get("plans") ?? {},
      audit: got.get("audit") ?? { head: GENESIS, count: 0 },
    };
  }

  async event(audit, kind, data) {
    audit.head = await sha256Hex(audit.head + canonical({ kind, ...data }));
    audit.count += 1;
    return audit.head;
  }

  async save(parts) {
    await this.storage.put(parts);
  }

  getPlan(plans, id) {
    return plans[id] ?? fail("PLAN_NOT_FOUND");
  }

  async proofgate_status() {
    const { state, plans, audit } = await this.load();
    return {
      service: "HERMX ProofGate · Recall",
      mode: "CLEAN_ROOM_DEMO",
      runtime: "cloudflare-worker",
      approval_required_for: GATED_ACTIONS,
      routine_tools: ROUTINE_TOOLS,
      card_count: Object.keys(state.cards).length,
      plan_count: Object.keys(plans).length,
      audit_count: audit.count,
      audit_head: audit.head,
      state_sha256: await digest(state),
    };
  }

  async progress() {
    const { state } = await this.load();
    const day = today();
    const topics = {};
    for (const c of Object.values(state.cards)) {
      const t = (topics[c.topic] ??= { cards: 0, learned: 0, due: 0 });
      t.cards += 1;
      t.learned += c.repetitions >= 3 ? 1 : 0;
      t.due += c.due <= day ? 1 : 0;
    }
    const sum = (k) => Object.values(topics).reduce((a, t) => a + t[k], 0);
    const [total, learned, due] = [sum("cards"), sum("learned"), sum("due")];
    const n = Object.keys(topics).length;
    return {
      total, learned, due, topics,
      say: `You have ${total} cards across ${n} topic${n === 1 ? "" : "s"}, ${learned} well learned and ${due} due now.`,
    };
  }

  async next_review({ topic = "" } = {}) {
    const { state } = await this.load();
    const day = today();
    const due = Object.values(state.cards)
      .filter((c) => c.due <= day && (!topic || c.topic === topic))
      .sort((a, b) => (a.due + a.id < b.due + b.id ? -1 : 1));
    if (!due.length) return { done: true, say: "Nothing is due right now. Nice work." };
    const c = due[0];
    return {
      done: false, card_id: c.id, topic: c.topic, question: c.front,
      say: `Fill in the blank. ${c.front.replace(BLANK, "blank")}`,
    };
  }

  async grade_answer({ card_id, answer }) {
    const { state, audit } = await this.load();
    const card = state.cards[card_id] ?? fail("CARD_NOT_FOUND");
    const [score, feedback] = grade(card.back, String(answer).slice(0, 200));
    const s = review(score, card.repetitions, card.interval_days, card.easiness, today());
    Object.assign(card, { repetitions: s.repetitions, interval_days: s.intervalDays, easiness: s.easiness, due: s.due });
    const head = await this.event(audit, "review.graded", { card_id, grade: score });
    await this.save({ state, audit });
    const when = s.intervalDays === 1 ? "tomorrow" : `in ${s.intervalDays} days`;
    return {
      card_id, grade: score, correct_answer: card.back, next_due: card.due, audit_head: head,
      say: `${feedback} The answer is ${card.back}. Next review ${when}.`,
    };
  }

  async plan_change({ action, topic, source = "", reason = "" }) {
    if (!GATED_ACTIONS.includes(action)) fail("ACTION_NOT_ALLOWED");
    if (!TOPIC_RE.test(topic ?? "")) fail("TOPIC_INVALID");
    const { state, plans, audit } = await this.load();
    const before = topicSlice(state, topic);
    const beforeCount = Object.keys(before).length;
    let payload = {};
    let summary;
    if (action === "import_deck") {
      if (!String(source).trim() || source.length > MAX_SOURCE_CHARS) fail("SOURCE_INVALID");
      const fresh = (await makeCards(source, topic, MAX_CARDS_PER_IMPORT)).filter((c) => !before[c.id]);
      if (!fresh.length) fail("NO_NEW_CARDS");
      if (Object.keys(state.cards).length + fresh.length > MAX_TOTAL_CARDS) fail("CAPACITY_EXCEEDED");
      payload = { cards: fresh };
      summary = `import ${fresh.length} new cards into '${topic}'`;
    } else if (!beforeCount) {
      fail("TOPIC_NOT_FOUND");
    } else {
      const verb = action === "reset_topic" ? "reset the schedule of" : "permanently delete";
      summary = `${verb} ${beforeCount} cards in '${topic}'`;
    }
    const hex = [...crypto.getRandomValues(new Uint8Array(6))].map((b) => b.toString(16).padStart(2, "0")).join("");
    const plan_id = `pg_${hex}`;
    const code = plan_id.slice(3, 9).toUpperCase();
    const plan = {
      plan_id, action, topic, reason: String(reason).trim().slice(0, 240), payload,
      effect_summary: summary, effective_date: today(), before_count: beforeCount,
      before_digest: await digest(before), status: "PLANNED", requires_approval: true,
      approval_code: code, created_at: now(), audit: ["plan.created"],
    };
    plan.after_digest = await digest(topicSlice(applyPlan(state, plan), topic));
    plans[plan_id] = plan;
    const ids = Object.keys(plans);
    for (const old of ids.slice(0, Math.max(0, ids.length - MAX_PLANS))) delete plans[old];
    await this.event(audit, "plan.created", { plan_id, action, topic });
    await this.save({ plans, audit });
    return {
      plan_id, action, topic, effect_summary: summary, before_count: beforeCount,
      before_digest: plan.before_digest, after_digest: plan.after_digest,
      preview: (payload.cards ?? []).slice(0, 3).map((c) => c.front), status: "PLANNED",
      approval_phrase: `APPROVE ${code}`,
      say: `I planned to ${summary}. Nothing has changed yet. To proceed, say: approve ${code.split("").join(" ")}.`,
    };
  }

  async approve_change({ plan_id, approval_phrase }) {
    const { plans, audit } = await this.load();
    const plan = this.getPlan(plans, plan_id);
    if (plan.status !== "PLANNED") fail("PLAN_NOT_APPROVABLE");
    // Spacing/case-insensitive so a spelled-out voice code still matches.
    if (String(approval_phrase).toUpperCase().replace(/\s+/g, "") !== "APPROVE" + plan.approval_code) {
      await this.event(audit, "approval.rejected", { plan_id });
      await this.save({ audit });
      fail("APPROVAL_MISMATCH");
    }
    plan.status = "APPROVED";
    plan.approved_at = now();
    plan.audit.push("approval.accepted");
    await this.event(audit, "plan.approved", { plan_id });
    await this.save({ plans, audit });
    return { plan_id, status: "APPROVED", say: "Approved. I'll re-check the current state right before making the change." };
  }

  async execute_change({ plan_id }) {
    const { state, plans, audit } = await this.load();
    const plan = this.getPlan(plans, plan_id);
    if (plan.status !== "APPROVED") fail("APPROVAL_REQUIRED");
    if ((await digest(topicSlice(state, plan.topic))) !== plan.before_digest) {
      plan.status = "BLOCKED_DRIFT";
      plan.audit.push("execution.blocked_drift");
      await this.event(audit, "plan.blocked_drift", { plan_id });
      await this.save({ plans, audit });
      fail("STATE_DRIFT");
    }
    const next = applyPlan(state, plan);
    next.last_change = plan_id;
    plan.status = "EXECUTED";
    plan.executed_at = now();
    plan.audit.push("execution.completed");
    const head = await this.event(audit, "plan.executed", { plan_id });
    await this.save({ state: next, plans, audit });
    return {
      plan_id, status: "EXECUTED", effect_summary: plan.effect_summary,
      card_count: Object.keys(next.cards).length, audit_head: head,
      say: `Done. I ${plan.effect_summary.replace("permanently ", "")}.`,
    };
  }

  async verify_change({ plan_id }) {
    const { state, plans, audit } = await this.load();
    const plan = this.getPlan(plans, plan_id);
    const topicDigest = await digest(topicSlice(state, plan.topic));
    const ok = plan.status === "EXECUTED" && topicDigest === plan.after_digest && state.last_change === plan_id;
    plan.audit.push(ok ? "verification.passed" : "verification.failed");
    const head = await this.event(audit, ok ? "plan.verified" : "plan.verify_failed", { plan_id });
    await this.save({ plans, audit });
    return {
      plan_id, verified: ok, status: ok ? "VERIFIED" : "NOT_VERIFIED",
      expected_topic_sha256: plan.after_digest, actual_topic_sha256: topicDigest,
      state_sha256: await digest(state), audit_head: head, checked_at: now(),
      say: ok ? "Verified. The result matches the approved plan."
        : "Verification failed: the current state doesn't match the approved plan.",
    };
  }
}
