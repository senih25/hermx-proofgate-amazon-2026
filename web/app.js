const run = document.querySelector("#run");
const output = document.querySelector("#output");
const state = document.querySelector("#state");

function setState(kind, text) {
  state.className = "pill " + kind;
  state.textContent = text;
}

run.addEventListener("click", async () => {
  run.disabled = true;
  setState("running", "RUNNING");
  output.textContent = "Connecting to the live MCP endpoint…";
  try {
    const response = await fetch("/api/run", { method: "POST" });
    const data = await response.json();
    output.textContent = data.output || "No output returned.";
    if (data.ok) {
      setState("pass", "VERIFIED");
    } else {
      setState("fail", "FAILED");
    }
  } catch (error) {
    output.textContent = String(error);
    setState("fail", "FAILED");
  } finally {
    run.disabled = false;
  }
});
