"""The live demo (Cloudflare Worker, JS) must extract and grade exactly like the
Python reference server. Skipped when Node.js isn't installed."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from learning import grade, make_cards

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [
    (
        "MCP is the Model Context Protocol, an open standard that connects agents to tools. "
        "Streamable HTTP is the remote transport defined in the 2025-11-25 specification. "
        "Alexa+ can reach a self-hosted server through Agent Skills. "
        "SM-2 schedules every card so that difficult cards return sooner. "
        "ProofGate re-checks a SHA-256 digest of the topic right before any approved change.",
        "mcp",
    ),
    (
        "Kubernetes schedules Pods onto Nodes.\nA Deployment keeps the desired number of replicas running!\n"
        "Services give a stable virtual IP to a changing set of Pods? Short line. "
        "The kube-apiserver validates and configures data for API objects.",
        "k8s",
    ),
]
GRADES = [
    ("Streamable", "streamable"), ("Streamable", "I think it's streamable"), ("Streamable", "streamabel"),
    ("Streamable", "websocket"), ("2025-11-25", "2025 11 25"), ("MCP", ""), ("SHA-256", "sha 256"),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_js_matches_python():
    proc = subprocess.run(
        ["node", str(ROOT / "worker" / "test" / "parity.mjs")],
        input=json.dumps({"sources": SOURCES, "grades": GRADES}),
        capture_output=True, text=True, encoding="utf-8", check=True, timeout=60,
    )
    js = json.loads(proc.stdout)
    assert js["cards"] == [make_cards(text, topic) for text, topic in SOURCES]
    assert [tuple(g) for g in js["grades"]] == [grade(e, a) for e, a in GRADES]
    assert all(js["cards"]), "every source should produce cards"
