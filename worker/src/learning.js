// Port of learning.py: deterministic cloze cards + spoken-answer grading.
const STOPWORDS = new Set(
  ("about above after again against also because been before being below between both cannot could " +
    "does doing down during each every from further have having here into itself just more most must " +
    "only other over same should some such than that their them then there these they this those " +
    "through under until used uses using very what when where which while will with would your").split(" "),
);
const SENTENCE_SPLIT = /(?<=[.!?])\s+|\n+/;
const WORD = /[A-Za-z0-9][A-Za-z0-9+#-]{2,}/g;
export const BLANK = "_____";

const isUpper = (w) => /[A-Za-z]/.test(w) && w === w.toUpperCase();
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function score(word, index) {
  const technical = /\d/.test(word) || isUpper(word);
  const proper = /[A-Z]/.test(word[0]) && index > 0;
  return [technical ? 2 : proper ? 1 : 0, word.length];
}

export async function sha256Hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function makeCards(source, topic, limit = 8) {
  const cards = [];
  const seen = new Set();
  for (const raw of source.split(SENTENCE_SPLIT)) {
    const sentence = raw.split(/\s+/).filter(Boolean).join(" ");
    if (sentence.length < 25 || sentence.length > 220) continue;
    const words = [...sentence.matchAll(WORD)]
      .map((m, i) => [i, m[0]])
      .filter(([, w]) => !STOPWORDS.has(w.toLowerCase()) && (w.length >= 4 || isUpper(w)));
    if (!words.length) continue;
    let best = words[0];
    for (const cand of words.slice(1)) {
      const [a, b] = [score(cand[1], cand[0]), score(best[1], best[0])];
      if (a[0] > b[0] || (a[0] === b[0] && a[1] > b[1])) best = cand;
    }
    const answer = best[1];
    const pattern = new RegExp(`(?<![A-Za-z0-9])${escapeRe(answer)}(?![A-Za-z0-9])`);
    const question = sentence.replace(pattern, BLANK);
    if (!question.includes(BLANK)) continue;
    const id = "c_" + (await sha256Hex(`${topic}|${question}`)).slice(0, 10);
    if (seen.has(id)) continue;
    seen.add(id);
    cards.push({ id, front: question, back: answer });
    if (cards.length >= limit) break;
  }
  return cards;
}

const norm = (t) => t.toLowerCase().replace(/[^a-z0-9]/g, "");

function similarity(a, b) {
  if (!a || !b) return 0;
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] !== b[j - 1] ? 1 : 0)));
    }
    prev = cur;
  }
  return 1 - prev[b.length] / Math.max(a.length, b.length);
}

export function grade(expected, answer) {
  const target = norm(expected);
  const tokens = answer.split(/\s+/).map(norm).filter(Boolean);
  const joined = norm(answer);
  if (!tokens.length) return [0, "I didn't catch an answer."];
  if (tokens.includes(target) || joined === target) return [5, "Exactly right."];
  const best = Math.max(...tokens.map((t) => similarity(target, t)), similarity(target, joined));
  if (joined.includes(target) || best >= 0.85) return [4, "Correct, close enough."];
  if (best >= 0.7) return [3, "Almost — watch the exact term."];
  return [1, "Not quite."];
}
