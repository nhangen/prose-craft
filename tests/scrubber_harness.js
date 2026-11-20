// Runs the inline URL scrubber from site/index.html against a stub window and
// prints the resulting URL, replaceState calls, and GA disable flag. Usage:
//   node scrubber_harness.js <index.html> '<json: {href, replaceState?}>'
// replaceState: "ok" (default), "throw", or "noop" (returns without changing the URL).
"use strict";
const fs = require("fs");
const vm = require("vm");

const [htmlPath, rawSpec] = process.argv.slice(2);
const spec = JSON.parse(rawSpec);
const html = fs.readFileSync(htmlPath, "utf8");

const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
const scrubber = scripts.find((s) => s.includes("history.replaceState"));
if (!scrubber) throw new Error("no inline scrubber script in index.html");

let href = spec.href;
const calls = [];
const state = { kept: true };
const window = {
  get location() { return new URL(href); },
  history: {
    state,
    replaceState(s, _title, url) {
      calls.push({ sameState: s === state, url });
      if (spec.replaceState === "throw") throw new Error("SecurityError");
      if (spec.replaceState === "noop") return;
      href = new URL(url, href).href;
    },
  },
};

vm.runInNewContext(scrubber, { window, URL, URLSearchParams });
process.stdout.write(JSON.stringify({
  href,
  calls,
  disabled: window["ga-disable-G-TC0R2KF0H9"] === true,
}));
