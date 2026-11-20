// Loads site/app.js against a stub DOM and reports the workbench href at
// setup plus the URL the click handler would navigate to after each input
// event. Usage:
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

function anything(props = {}) {
  const target = function () {};
  Object.assign(target, props);
  return new Proxy(target, {
    get(t, k) {
      if (Object.prototype.hasOwnProperty.call(t, k)) return t[k];
      if (k === Symbol.iterator) return function* () {};
      if (k === Symbol.toPrimitive) return () => "";
      if (k === "length") return 0;
      return anything();
    },
    set(t, k, v) { t[k] = v; return true; },
    apply() { return anything(); },
  });
}

const listeners = {};
const navigations = [];
function element(id, props) {
  return anything({
    ...props,
    addEventListener(type, fn) { (listeners[`${id}:${type}`] ||= []).push(fn); },
  });
}

const baseHref = anchorHref("chk-workbench");
const src = element("chk-src", {
  defaultValue: textareaDefault("chk-src"),
  value: spec.initial === undefined ? textareaDefault("chk-src") : spec.initial,
});
// The property and the attribute share one store, as on a real anchor, so a
// draft written through either route shows up in hrefWrites.
const attrs = { href: baseHref };
const hrefWrites = [];
function writeAttr(name, value) {
  if (name === "href") hrefWrites.push(String(value));
  attrs[name] = String(value);
}
const link = element("chk-workbench", {
  getAttribute(name) { return name in attrs ? attrs[name] : null; },
  setAttribute: writeAttr,
});
Object.defineProperty(link, "href", {
  get() { return attrs.href; },
  set(value) { writeAttr("href", value); },
  enumerable: true,
  configurable: true,
});
const elements = { "chk-src": src, "chk-workbench": link };

const document = anything({
  getElementById(id) { return elements[id] || (elements[id] = element(id, {})); },
  addEventListener() {},
});
const context = {
  document,
  window: {
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
  return { navigated: navigations[0] || null, prevented: event.defaultPrevented };
}

// Simulate a left mouse click on the workbench link for the initial value
// and each input value, recording where the click handler sends the browser.
out.navigates = [];
out.prevented = [];
const allValues = [spec.initial, ...spec.inputs].filter((v) => v !== undefined);
for (const value of allValues) {
  src.value = value;
  const result = click("click");
  out.navigates.push(result.navigated);
  out.prevented.push(result.prevented);
}
src.value = "My draft.";
out.modified = {
  meta: click("click", { metaKey: true }),
  ctrl: click("click", { ctrlKey: true }),
  shift: click("click", { shiftKey: true }),
  alt: click("click", { altKey: true }),
  middleAuxclick: click("auxclick", { button: 1 }),
};
out.hrefWrites = hrefWrites;
process.stdout.write(JSON.stringify(out));
