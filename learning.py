"""Deterministic flashcard extraction and spoken-answer grading.

No LLM and no network: the same source text always yields the same cloze cards,
which is what lets ProofGate compute the expected post-import state digest at
plan time. `worker/src/learning.js` is a line-for-line port; the live
conformance run (`demo_flow.py --url ...`) checks both behave the same.
"""
from __future__ import annotations

import hashlib
import re

STOPWORDS = {
    "about", "above", "after", "again", "against", "also", "because", "been", "before",
    "being", "below", "between", "both", "cannot", "could", "does", "doing", "down",
    "during", "each", "every", "from", "further", "have", "having", "here", "into",
    "itself", "just", "more", "most", "must", "only", "other", "over", "same", "should",
    "some", "such", "than", "that", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "under", "until", "used", "uses", "using", "very",
    "what", "when", "where", "which", "while", "will", "with", "would", "your",
}
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#-]{2,}")
BLANK = "_____"


def _score(word: str, index: int) -> tuple[int, int]:
    technical = any(c.isdigit() for c in word) or word.isupper()
    proper = word[0].isupper() and index > 0
    return (2 if technical else 1 if proper else 0, len(word))


def make_cards(source: str, topic: str, limit: int = 8) -> list[dict]:
    """Turn source text into cloze cards: one blanked key term per sentence."""
    cards: list[dict] = []
    seen: set[str] = set()
    for raw in SENTENCE_SPLIT.split(source):
        sentence = " ".join(raw.split())
        if not 25 <= len(sentence) <= 220:
            continue
        words = [
            (i, w) for i, w in enumerate(WORD.findall(sentence))
            if w.lower() not in STOPWORDS and (len(w) >= 4 or w.isupper())
        ]
        if not words:
            continue
        index, answer = max(words, key=lambda iw: _score(iw[1], iw[0]))
        pattern = rf"(?<![A-Za-z0-9]){re.escape(answer)}(?![A-Za-z0-9])"
        question = re.sub(pattern, BLANK, sentence, count=1)
        if BLANK not in question:
            continue
        card_id = "c_" + hashlib.sha256(f"{topic}|{question}".encode()).hexdigest()[:10]
        if card_id in seen:
            continue
        seen.add(card_id)
        cards.append({"id": card_id, "front": question, "back": answer})
        if len(cards) >= limit:
            break
    return cards


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b))


def grade(expected: str, answer: str) -> tuple[int, str]:
    """Grade a spoken answer 0-5 against the cloze term."""
    target = _norm(expected)
    tokens = [_norm(t) for t in re.split(r"\s+", answer) if _norm(t)]
    joined = _norm(answer)
    if not tokens:
        return 0, "I didn't catch an answer."
    if target in tokens or joined == target:
        return 5, "Exactly right."
    best = max([_similarity(target, t) for t in tokens] + [_similarity(target, joined)])
    if target in joined or best >= 0.85:
        return 4, "Correct, close enough."
    if best >= 0.7:
        return 3, "Almost — watch the exact term."
    return 1, "Not quite."


def _demo() -> None:
    src = ("MCP is the Model Context Protocol for agent tools. "
           "Streamable HTTP is the remote transport defined in the 2025-11-25 specification. "
           "Short.")
    cards = make_cards(src, "mcp")
    assert len(cards) == 2, cards
    assert cards == make_cards(src, "mcp"), "extraction must be deterministic"
    assert all(BLANK in c["front"] and c["back"] not in c["front"] for c in cards), cards
    assert [c["back"] for c in cards] == ["MCP", "2025-11-25"], cards
    assert grade("Streamable", "streamable")[0] == 5
    assert grade("Streamable", "I think it's streamable")[0] == 5
    assert grade("Streamable", "streamabel")[0] >= 3
    assert grade("Streamable", "websocket")[0] <= 1
    assert grade("Streamable", "")[0] == 0
    print("learning self-check ok")


if __name__ == "__main__":
    _demo()
