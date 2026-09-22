// Emits the JS implementation's cards and grades for the inputs on stdin, so
// tests/test_parity.py can compare them with the Python implementation.
import { makeCards, grade } from "../src/learning.js";

let raw = "";
for await (const chunk of process.stdin) raw += chunk;
const { sources, grades } = JSON.parse(raw);
const out = {
  cards: await Promise.all(sources.map(([text, topic]) => makeCards(text, topic))),
  grades: grades.map(([expected, answer]) => grade(expected, answer)),
};
process.stdout.write(JSON.stringify(out));
