// Loads site/app.js against a stub DOM, simulates input events and clicks on
// the workbench link, and reports the link's href, where each click
// navigates, whether it cancelled the default, and every write the app made
// to the link. Usage:
//   node workbench_harness.js <app.js> '<json: {initial, inputs}>'
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
function element(id, props, onSet = null) {
  return anything({
    ...props,
    addEventListener(type, fn) { (listeners[`${id}:${type}`] ||= []).push(fn); },
  }, onSet);
}

const baseHref = anchorHref("chk-workbench");
const src = element("chk-src", {
  defaultValue: textareaDefault("chk-src"),
  value: spec.initial === undefined ? textareaDefault("chk-src") : spec.initial,
});
// GA4 reads the link's href, id and classes, and on a real anchor setting
// hash, search or pathname rewrites href, so any write to the link counts.
const attrs = { href: baseHref };
const linkWrites = [];
const recordWrite = (name, value) => linkWrites.push(`${name}=${value}`);
const link = element("chk-workbench", {
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
const elements = { "chk-src": src, "chk-workbench": link };

const clipboardWrites = [];
let clipboardContents = spec.clipboardInitial || "";
const navigatorObj = {
  clipboard: {
    writeText(text) {
      clipboardWrites.push(String(text));
      clipboardContents = String(text);
      return Promise.resolve();
    },
    readText() {
      return Promise.resolve(clipboardContents);
    },
  },
};

const document = anything({
  getElementById(id) { return elements[id] || (elements[id] = element(id, {})); },
  addEventListener() {},
});
const context = {
  document,
  navigator: navigatorObj,
  window: {
    navigator: navigatorObj,
    location: {
      href: "https://prosecraft.dev/",
      origin: "https://prosecraft.dev",
      assign(url) { navigations.push(url); },
    },
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

const out = { example: src.defaultValue, base: baseHref, afterSetup: link.href, afterInput: [] };
// A click before any input, with the textarea still holding its initial or
// example text.
out.setupClick = click("click").navigated;
out.setupClipboardWrites = clipboardWrites.slice();
clipboardWrites.length = 0;
for (const value of spec.inputs || []) {
  src.value = value;
  (listeners["chk-src:input"] || []).forEach((fn) => fn({ target: src }));
  out.afterInput.push(link.href);
}

function click(type, overrides = {}) {
  navigations.length = 0;
  const event = {
    type,
    target: link,
    button: 0,
    metaKey: false, ctrlKey: false, shiftKey: false, altKey: false,
    defaultPrevented: false,
    preventDefault() { this.defaultPrevented = true; },
    ...overrides,
  };
  (listeners[`chk-workbench:${type}`] || []).forEach((fn) => fn(event));
  const isPrimaryClick = event.type === "click" && event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
  return { navigated: navigations[0] || (event.defaultPrevented || !isPrimaryClick ? null : link.href), prevented: event.defaultPrevented };
}

// Simulate a left mouse click on the workbench link for the initial value
// and each input value, recording where the click handler sends the browser.
out.navigates = [];
out.prevented = [];
const allValues = [spec.initial, ...(spec.inputs || [])].filter((v) => v !== undefined);
for (const value of allValues) {
  src.value = value;
  const result = click("click");
  out.navigates.push(result.navigated);
  out.prevented.push(result.prevented);
}
out.clipboardWrites = clipboardWrites.slice();
src.value = "My draft.";
out.modified = {
  meta: click("click", { metaKey: true }),
  ctrl: click("click", { ctrlKey: true }),
  shift: click("click", { shiftKey: true }),
  alt: click("click", { altKey: true }),
  middleClick: click("click", { button: 1 }),
  middleAuxclick: click("auxclick", { button: 1 }),
};
out.linkWrites = linkWrites;
process.stdout.write(JSON.stringify(out));
