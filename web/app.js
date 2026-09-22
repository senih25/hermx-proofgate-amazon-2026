// Recall web client: an Alexa+ experience simulator that is itself a real MCP
// client. Every action below is a JSON-RPC call to this origin's /mcp endpoint.
const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const quiet = params.has("quiet");

const SAMPLE =
  "MCP is the Model Context Protocol, an open standard that connects agents to tools. " +
  "Streamable HTTP is the remote transport defined in the 2025-11-25 specification. " +
  "Alexa+ can reach a self-hosted server through Agent Skills. " +
  "SM-2 schedules every card so that difficult cards return sooner. " +
  "ProofGate re-checks a SHA-256 digest of the topic right before any approved change.";

function sandboxId() {
  const fromUrl = params.get("sandbox");
  if (fromUrl) return fromUrl;
  let id = null;
  try { id = sessionStorage.getItem("recall-sandbox"); } catch {}
  if (!id) {
    id = "v-" + Math.random().toString(36).slice(2, 10);
    try { sessionStorage.setItem("recall-sandbox", id); } catch {}
  }
  return id;
}
const sandbox = sandboxId();
const endpoint = `/mcp?sandbox=${encodeURIComponent(sandbox)}`;

// ---- MCP over Streamable HTTP ------------------------------------------------
let rpcId = 0;
let protocol = "2025-11-25";

async function post(body, withVersion = true) {
  const headers = { "content-type": "application/json", accept: "application/json, text/event-stream" };
  if (withVersion) headers["mcp-protocol-version"] = protocol;
  return fetch(endpoint, { method: "POST", headers, body: JSON.stringify(body) });
}

async function rpc(method, params, withVersion = true) {
  const res = await post({ jsonrpc: "2.0", id: ++rpcId, method, params }, withVersion);
  const msg = await res.json();
  if (msg.error) throw new Error(msg.error.message);
  return msg.result;
}

class ToolError extends Error {}

async function call(name, args = {}) {
  const result = await rpc("tools/call", { name, arguments: args });
  const text = (result.content || []).map((c) => c.text || "").join("\n");
  if (result.isError) {
    const code = (text.match(/([A-Z][A-Z_]{3,})(?::[^\n]*)?\s*$/) || [])[1] || text;
    throw new ToolError(code);
  }
  return result.structuredContent || JSON.parse(text);
}

async function connect() {
  try {
    const init = await rpc("initialize", {
      protocolVersion: protocol,
      capabilities: {},
      clientInfo: { name: "recall-alexa-simulator", version: "0.2.0" },
    }, false);
    protocol = init.protocolVersion;
    await post({ jsonrpc: "2.0", method: "notifications/initialized" });
    const { tools } = await rpc("tools/list", {});
    $("conn").textContent = `Connected over MCP ${protocol}, ${tools.length} tools`;
    $("conn").className = "conn live";
    await refresh();
  } catch (err) {
    $("conn").textContent = "MCP server unreachable. Start it with python server.py";
    $("conn").className = "conn down";
  }
}

// ---- UI state ---------------------------------------------------------------
let currentCard = null;
let pendingPlan = null;

function speak(text) {
  if (quiet || !("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "en-US";
  u.rate = 1.02;
  u.onstart = () => $("ring").classList.add("speaking");
  u.onend = () => $("ring").classList.remove("speaking");
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

function line(who, text, tone = "") {
  const li = document.createElement("li");
  li.className = who === "You" ? "you" : `recall ${tone}`;
  const label = document.createElement("span");
  label.className = "who";
  label.textContent = who;
  li.append(label, document.createTextNode(text));
  $("transcript").append(li);
  li.scrollIntoView({ block: "end" });
  if (who !== "You") speak(text);
}

function ledger(label, head, kind = "") {
  const li = document.createElement("li");
  li.className = kind;
  const code = document.createElement("span");
  code.className = "mono";
  code.textContent = head ? head.slice(0, 12) + "…" : "";
  li.append(document.createTextNode(label), code);
  $("ledger").prepend(li);
}

async function refresh() {
  const p = await call("progress");
  $("stTotal").textContent = p.total;
  $("stDue").textContent = p.due;
  $("stLearned").textContent = p.learned;
  return (await call("proofgate_status")).audit_head;
}

function setStep(step, state) {
  const li = document.querySelector(`#track [data-step="${step}"]`);
  li.className = state;
}

function showPlan(plan) {
  const card = $("plan");
  card.hidden = false;
  card.classList.remove("enter");
  void card.offsetWidth;
  card.classList.add("enter");
  $("planTitle").textContent = {
    import_deck: "Import a deck", reset_topic: "Reset a topic", delete_topic: "Delete a topic",
  }[plan.action];
  $("planId").textContent = plan.plan_id;
  $("planSummary").textContent = `Recall will ${plan.effect_summary}. Nothing has changed yet.`;
  $("planPreview").replaceChildren(...plan.preview.map((q) => Object.assign(document.createElement("li"), { textContent: q })));
  $("planPhrase").textContent = plan.approval_phrase;
  $("planBefore").textContent = `${plan.before_count} cards, ${plan.before_digest.slice(0, 10)}…`;
  $("planAfter").textContent = `${plan.after_digest.slice(0, 10)}…`;
  ["plan", "approve", "execute", "verify"].forEach((s) => setStep(s, ""));
  setStep("plan", "done");
  setStep("approve", "active");
  $("stamp").hidden = true;
}

function stamp(word, detail, blocked) {
  const s = $("stamp");
  $("stampWord").textContent = word;
  $("stampHash").textContent = detail;
  s.className = "stamp press" + (blocked ? " blocked" : "");
  s.hidden = false;
}

function explain(code) {
  return {
    APPROVAL_MISMATCH: "That isn't the approval phrase for this plan, so nothing changed. Say the exact phrase on the card.",
    APPROVAL_REQUIRED: "This plan isn't approved, so I won't run it.",
    STATE_DRIFT: "Blocked. The topic changed after this plan was made, so your approval no longer matches what you saw. Nothing was changed; plan again if you still want this.",
    TOPIC_NOT_FOUND: "I don't have a topic with that name yet.",
    NO_NEW_CARDS: "I couldn't find anything new to learn in that text.",
    SOURCE_INVALID: "Add some text to learn from first (up to 4,000 characters).",
    TOPIC_INVALID: "Topic names use lowercase letters, numbers and dashes.",
    CAPACITY_EXCEEDED: "This demo sandbox is full. Delete a topic first.",
    CARD_NOT_FOUND: "That card is gone. Say quiz me for the next one.",
  }[code] || `That didn't work (${code}).`;
}

// ---- Intents (a tiny stand-in for Alexa+ language understanding) ------------
function intent(text) {
  const t = text.trim().toLowerCase();
  let m;
  if (pendingPlan && /^(approve|yes|yeah|ok|okay|sure|go ahead|do it)\b/.test(t)) return { kind: "approve" };
  if ((m = t.match(/^(?:learn|import|add)\b.*?\bas\s+([a-z0-9-]+)/))) return { kind: "import", topic: m[1] };
  if (/^(?:learn|import|add)\b/.test(t)) return { kind: "import", topic: "general" };
  if ((m = t.match(/^(?:reset|restart)\s+([a-z0-9-]+)/))) return { kind: "reset", topic: m[1] };
  if ((m = t.match(/^(?:delete|remove|forget)\s+([a-z0-9-]+)/))) return { kind: "delete", topic: m[1] };
  if ((m = t.match(/^quiz me(?:\s+on\s+([a-z0-9-]+))?/))) return { kind: "quiz", topic: m[1] || "" };
  if (/how am i doing|progress/.test(t)) return { kind: "progress" };
  if (currentCard) return { kind: "answer" };
  return { kind: "unknown" };
}

async function handle(text) {
  line("You", text);
  const it = intent(text);
  $("ring").classList.add("thinking");
  try {
    if (it.kind === "import" || it.kind === "reset" || it.kind === "delete") {
      const plan = await call("plan_change", {
        action: { import: "import_deck", reset: "reset_topic", delete: "delete_topic" }[it.kind],
        topic: it.topic,
        source: it.kind === "import" ? $("sourceText").value : "",
        reason: "Requested by voice",
      });
      pendingPlan = plan;
      showPlan(plan);
      line("Recall", plan.say);
      ledger(`Plan created: ${plan.effect_summary}`, await refresh(), "gate");
    } else if (it.kind === "approve") {
      await approveFlow(text);
    } else if (it.kind === "quiz") {
      const q = await call("next_review", { topic: it.topic });
      currentCard = q.done ? null : q;
      $("study").hidden = q.done;
      if (!q.done) {
        $("studyTopic").textContent = `Topic: ${q.topic}`;
        $("studyQ").textContent = q.question;
        $("studyA").textContent = "";
      }
      line("Recall", q.say);
    } else if (it.kind === "answer") {
      const g = await call("grade_answer", { card_id: currentCard.card_id, answer: text });
      $("studyA").textContent = `Answer: ${g.correct_answer}. Graded ${g.grade} of 5, next review ${g.next_due}.`;
      line("Recall", g.say, g.grade >= 3 ? "done" : "");
      currentCard = null;
      ledger(`Review graded ${g.grade}/5 (routine, no approval needed)`, g.audit_head);
      await refresh();
    } else if (it.kind === "progress") {
      line("Recall", (await call("progress")).say);
    } else {
      line("Recall", "Try: learn this as mcp, quiz me, how am I doing, reset mcp, or delete mcp.");
    }
  } catch (err) {
    if (!(err instanceof ToolError)) throw err;
    line("Recall", explain(err.message), "blocked");
  } finally {
    $("ring").classList.remove("thinking");
  }
}

async function approveFlow(phrase) {
  const plan = pendingPlan;
  try {
    await call("approve_change", { plan_id: plan.plan_id, approval_phrase: phrase });
  } catch (err) {
    if (err instanceof ToolError) ledger("Approval rejected: phrase didn't match, nothing changed", await refresh(), "stop");
    throw err;
  }
  setStep("approve", "done");
  setStep("execute", "active");
  line("Recall", "Approved. Checking the topic hasn't changed, then making the change.");
  ledger("Plan approved with its exact phrase", await refresh(), "gate");
  pendingPlan = null;
  let done;
  try {
    done = await call("execute_change", { plan_id: plan.plan_id });
  } catch (err) {
    if (err instanceof ToolError && err.message === "STATE_DRIFT") {
      setStep("execute", "blocked");
      stamp("Blocked", "topic changed since plan", true);
      ledger("Execution blocked: state drift detected", await refresh(), "stop");
    }
    throw err;
  }
  setStep("execute", "done");
  setStep("verify", "active");
  ledger(`Executed: ${done.effect_summary}`, done.audit_head, "gate");
  const v = await call("verify_change", { plan_id: plan.plan_id });
  setStep("verify", v.verified ? "done" : "blocked");
  stamp(v.verified ? "Verified" : "Mismatch", `sha256 ${v.actual_topic_sha256.slice(0, 8)}`, !v.verified);
  line("Recall", v.say, v.verified ? "done" : "blocked");
  ledger(v.verified ? "Verified: result matches the approved plan" : "Verification failed", await refresh(), v.verified ? "gate" : "stop");
}

// ---- Voice input ------------------------------------------------------------
function listen() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    $("ringHint").textContent = "Voice input needs Chrome or Edge. You can type instead.";
    $("utter").focus();
    return;
  }
  const rec = new SR();
  rec.lang = "en-US";
  rec.interimResults = false;
  $("ring").classList.add("listening");
  $("ringHint").textContent = "Listening…";
  rec.onresult = (e) => handle(e.results[0][0].transcript);
  rec.onend = () => {
    $("ring").classList.remove("listening");
    $("ringHint").textContent = "Tap the ring and speak, or type below.";
  };
  rec.start();
}

// ---- Guided demo --------------------------------------------------------------
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

function answerFromSource(question) {
  const [pre, post] = question.split("_____").map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const m = $("sourceText").value.match(new RegExp(pre + "(\\S+?)" + post));
  return m ? m[1] : "I'm not sure";
}

async function typeAndSend(text, pause = 1800) {
  const input = $("utter");
  input.value = "";
  for (const ch of text) {
    input.value += ch;
    await wait(28);
  }
  await wait(250);
  input.value = "";
  await handle(text);
  await wait(pause);
}

async function guidedDemo() {
  $("guided").disabled = true;
  try {
    const topic = "mcp";
    await typeAndSend(`Learn this as ${topic}`, 2600);
    if (pendingPlan) {
      await typeAndSend("Yes, go ahead", 2600);
      const code = pendingPlan.approval_phrase.split(" ")[1];
      await typeAndSend(`Approve ${code.split("").join(" ")}`, 3200);
    }
    for (const answer of ["websocket", null]) {
      await typeAndSend(`Quiz me on ${topic}`, 2000);
      if (!currentCard) break;
      await typeAndSend(answer ?? answerFromSource(currentCard.question), 2600);
    }
    await typeAndSend(`Reset ${topic}`, 2400);
    await typeAndSend(`Quiz me on ${topic}`, 1600);
    if (currentCard) await typeAndSend(answerFromSource(currentCard.question), 2200);
    if (pendingPlan) {
      const code = pendingPlan.approval_phrase.split(" ")[1];
      await typeAndSend(`Approve ${code}`, 3200);
    }
    await typeAndSend("How am I doing?", 1200);
  } finally {
    $("guided").disabled = false;
  }
}

// ---- Wiring -----------------------------------------------------------------
$("sourceText").value = SAMPLE;
$("sandboxId").textContent = sandbox;
$("ring").addEventListener("click", listen);
$("guided").addEventListener("click", guidedDemo);
$("say").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("utter").value.trim();
  if (!text) return;
  $("utter").value = "";
  handle(text);
});
document.querySelectorAll(".chips [data-say]").forEach((b) => b.addEventListener("click", () => handle(b.dataset.say)));
line("Recall", "Hi, I'm Recall. Ask me to learn the text below, then quiz you on it. I'll ask before I change any deck.");
connect();
if (params.has("autoplay")) setTimeout(guidedDemo, 1500);
