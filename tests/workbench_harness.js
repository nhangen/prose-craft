// Loads site/app.js against a stub DOM, simulates input events and clicks on
// the Prose Craft Live link, and reports the link's href, what each click put
// on the clipboard, where it navigates, whether it cancelled the default, and
// every write the app made to the link. Usage:
//   node workbench_harness.js <app.js> '<json: {initial, inputs, clipboard}>'
// clipboard is "ok" (default), "reject" (writeText rejects) or "missing"
// (no navigator.clipboard).
"use strict";
const fs = require("fs");
const vm = require("vm");

const [appPath, rawSpec] = process.argv.slice(2);
const spec = JSON.parse(rawSpec);
const html = fs.readFileSync(require("path").join(require("path").dirname(appPath), "index.html"), "utf8");

function textareaDefault(id) {
  const m = html.match(new RegExp(`<textarea id="${id}"[^>]*>([\\s\\S]*?)</textarea>`));
  if (!m) throw new Error(`no <textarea id="${id}"> in index.html`);
  return m[1];
}

function anchorHref(id) {
  const tag = html.match(new RegExp(`<a\\b[^>]*\\bid="${id}"[^>]*>`));
  if (!tag) throw new Error(`no <a id="${id}"> in index.html`);
  return tag[0].match(/\bhref="([^"]*)"/)[1];
}

// onSet, when given, sees every property write on this object and on any
// object reached through it (link.hash, link.dataset.x, link.attributes...).
function anything(props = {}, onSet = null, path = "") {
  const target = function () {};
  Object.assign(target, props);
  return new Proxy(target, {
    get(t, k) {
      if (Object.prototype.hasOwnProperty.call(t, k)) return t[k];
      if (k === Symbol.iterator) return function* () {};
      if (k === Symbol.toPrimitive) return () => "";
      if (k === "length") return 0;
      return anything({}, onSet, `${path}${String(k)}.`);
    },
    set(t, k, v) {
      if (onSet) onSet(`${path}${String(k)}`, v);
      t[k] = v;
      return true;
    },
    apply() { return anything({}, onSet, path); },
  });
}

const listeners = {};
const navigations = [];
// Every clipboard write and navigation, in the order the app made them.
const events = [];
function element(id, props, onSet = null) {
  return anything({
    ...props,
    addEventListener(type, fn) { (listeners[`${id}:${type}`] ||= []).push(fn); },
  }, onSet);
}

const baseHref = anchorHref("chk-live");
const src = element("chk-src", {
  defaultValue: textareaDefault("chk-src"),
  value: spec.initial === undefined ? textareaDefault("chk-src") : spec.initial,
});
// GA4 reads the link's href, id and classes, and on a real anchor setting
// hash, search or pathname rewrites href, so any write to the link counts.
const attrs = { href: baseHref };
const linkWrites = [];
const recordWrite = (name, value) => linkWrites.push(`${name}=${value}`);
const link = element("chk-live", {
  getAttribute(name) { return name in attrs ? attrs[name] : null; },
  setAttribute(name, value) { recordWrite(`@${name}`, value); attrs[name] = String(value); },
  setAttributeNS(_ns, name, value) { recordWrite(`@${name}`, value); attrs[name] = String(value); },
  toggleAttribute(name) { recordWrite(`@${name}`, "toggled"); },
  removeAttribute(name) { recordWrite(`@${name}`, "removed"); delete attrs[name]; },
}, recordWrite);
Object.defineProperty(link, "href", {
  get() { return attrs.href; },
  set(value) { attrs.href = String(value); },
  enumerable: true,
  configurable: true,
});
const elements = { "chk-src": src, "chk-live": link };

const document = anything({
  getElementById(id) { return elements[id] || (elements[id] = element(id, {})); },
  addEventListener() {},
  execCommand(name) { events.push(`exec:${name}:${src.value}`); return true; },
});
const mode = spec.clipboard || "ok";
const navigator = mode === "missing" ? {} : {
  clipboard: {
    writeText(text) {
      if (mode === "reject") return Promise.reject(new Error("blocked"));
      events.push(`copy:${text}`);
      return Promise.resolve();
    },
  },
};
const context = {
  document,
  window: {
    location: {
      href: "https://prosecraft.dev/",
      origin: "https://prosecraft.dev",
      assign(url) { navigations.push(url); events.push(`go:${url}`); },
    },
    navigator,
  },
  localStorage: { getItem() { return null; }, setItem() {} },
  Element: function Element() {},
  HTMLAnchorElement: function HTMLAnchorElement() {},
  URL,
  console,
  setTimeout() {}, clearTimeout() {}, setInterval() {}, clearInterval() {},
  requestAnimationFrame() {}, cancelAnimationFrame() {},
};
context.globalThis = context;
vm.createContext(context);
const filterPath = require("path").join(require("path").dirname(appPath), "prose-filter.js");
vm.runInContext(fs.readFileSync(filterPath, "utf8"), context, { filename: filterPath });
vm.runInContext(fs.readFileSync(appPath, "utf8"), context, { filename: appPath });

(async () => {
const out = { example: src.defaultValue, base: baseHref, afterSetup: link.href, afterInput: [] };
// A click before any input, with the textarea still holding its initial or
// example text.
out.setupClick = (await click("click")).navigated;
for (const value of spec.inputs || []) {
  src.value = value;
  (listeners["chk-src:input"] || []).forEach((fn) => fn({ target: src }));
  out.afterInput.push(link.href);
}

async function click(type, overrides = {}) {
  navigations.length = 0;
  events.length = 0;
  const event = {
    type,
    target: link,
    button: 0,
    metaKey: false, ctrlKey: false, shiftKey: false, altKey: false,
    defaultPrevented: false,
    preventDefault() { this.defaultPrevented = true; },
    ...overrides,
  };
  (listeners[`chk-live:${type}`] || []).forEach((fn) => fn(event));
  // Let the clipboard promise chain settle before reading the outcome.
  for (let i = 0; i < 10; i++) await new Promise((resolve) => setImmediate(resolve));
  return { navigated: navigations[0] || null, prevented: event.defaultPrevented, events: [...events] };
}

// Simulate a left mouse click on the Prose Craft Live link for the initial value
// and each input value, recording where the click handler sends the browser.
out.navigates = [];
out.prevented = [];
out.events = [];
const allValues = [spec.initial, ...(spec.inputs || [])].filter((v) => v !== undefined);
for (const value of allValues) {
  src.value = value;
  const result = await click("click");
  out.navigates.push(result.navigated);
  out.prevented.push(result.prevented);
  out.events.push(result.events);
}
src.value = "My draft.";
out.modified = {
  meta: await click("click", { metaKey: true }),
  ctrl: await click("click", { ctrlKey: true }),
  shift: await click("click", { shiftKey: true }),
  alt: await click("click", { altKey: true }),
  middleClick: await click("click", { button: 1 }),
  middleAuxclick: await click("auxclick", { button: 1 }),
};
out.linkWrites = linkWrites;
process.stdout.write(JSON.stringify(out));
})().catch((err) => { console.error(err); process.exit(1); });
