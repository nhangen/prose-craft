(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const el = (tag, props, ...kids) => {
    const node = document.createElement(tag);
    Object.entries(props || {}).forEach(([k, v]) => {
      if (k === "style") node.style.cssText = v;
      else if (k === "text") node.textContent = v;
      else node.setAttribute(k, v);
    });
    kids.forEach((kid) => node.append(kid));
    return node;
  };

  function trackClick(event) {
    const target = event.target instanceof Element ? event.target.closest("a, button") : null;
    if (!target || typeof window.gtag !== "function") return;
    if (event.type === "auxclick" && (!(target instanceof HTMLAnchorElement) || event.button !== 1)) return;

    let destination;
    if (target instanceof HTMLAnchorElement) {
      const url = new URL(target.href, window.location.href);
      destination = url.origin === window.location.origin
        ? `${url.pathname}${url.hash}`
        : `${url.hostname}${url.pathname}`;
    }
    const section = target.closest("section, header, footer");
    const parameters = {
      element_type: target instanceof HTMLAnchorElement ? "link" : "button",
      element_label: (target.getAttribute("aria-label") || target.textContent || "").trim().slice(0, 80),
      page_location: `${window.location.origin}${window.location.pathname}`,
      page_referrer: document.referrer ? new URL(document.referrer).origin : "",
    };
    if (section?.id) parameters.section_id = section.id;
    if (destination) parameters.destination = destination;
    window.gtag("event", "site_click", parameters);
  }

  document.addEventListener("click", trackClick, true);
  document.addEventListener("auxclick", trackClick, true);

  const CHK_EXAMPLE = $("chk-src").value;

  const SAMPLES = [
    { label: "PR description",
      intake: "Write a PR description for a change that retries failed webhook deliveries with exponential backoff.",
      segs: [
        { t: "This PR adds retries for failed webhook deliveries. " },
        { t: "In the previous implementation, a single failed request dropped the event for good. ", f: "A single failed request used to drop the event for good. ", m: "sentence opens with an adverbial:" },
        { t: "Failures now back off exponentially — one second, then two, then four — up to five attempts. ", f: "Failures now back off exponentially (one second, then two, then four), up to five attempts. ", m: "dash used as punctuation in" },
        { t: "To avoid hammering a struggling endpoint, each delay carries up to 20% jitter. ", f: "Each delay carries up to 20% jitter so a struggling endpoint is not hammered. ", m: "sentence opens with an adverbial:" },
        { t: "Events that exhaust every attempt land in the dead-letter table with the last response body. " },
        { t: "If you rerun the migration, nothing changes for existing rows. ", f: "Rerunning the migration changes nothing for existing rows. ", m: "sentence opens with an adverbial:" },
        { t: "Tests cover the backoff schedule, the jitter bounds, and the dead-letter handoff." }
      ] },
    { label: "Email",
      intake: "Email my landlord that the heater has been out since Monday and ask for a repair date.",
      segs: [
        { t: "Hi Dana,\n\n" },
        { t: "Unfortunately, the heater in unit 4B has been out since Monday. ", f: "The heater in unit 4B has been out since Monday. ", m: "sentence opens with an adverbial:" },
        { t: "With nights dropping below 40 degrees — and a toddler in the apartment — I would like to get it fixed soon. ", f: "Nights are dropping below 40 degrees and we have a toddler in the apartment, so I would like it fixed soon. ", m: "sentence opens with an adverbial:" },
        { t: "Could you tell me which day this week a technician can come? " },
        { t: "In the meantime, I will run a space heater in the bedroom.", f: "I will run a space heater in the bedroom until then.", m: "sentence opens with an adverbial:" },
        { t: "\n\nThank you,\nSam" }
      ] },
    { label: "Story opening",
      intake: "Open a short story about a night ferry operator.",
      segs: [
        { t: "Quietly, Marta untied the last rope and let the ferry drift. ", f: "Marta untied the last rope and let the ferry drift. ", m: "sentence opens with an adverbial:" },
        { t: "The harbor lights thinned out behind her — one, then another, then none. ", f: "The harbor lights thinned out behind her: one, then another, then none. ", m: "dash used as punctuation in" },
        { t: "She had run this crossing for nineteen winters and kept a thermos of cold coffee on the dash for every one of them. " },
        { t: "While the engine warmed, she spoke to the empty deck as though someone were listening.", f: "She spoke to the empty deck as though someone were listening while the engine warmed.", m: "sentence opens with an adverbial:" }
      ] },
    { label: "README intro",
      intake: "Write the opening paragraph for the README of a CLI that syncs dotfiles.",
      segs: [
        { t: "To keep your machines in step, dotsync mirrors your config files through a git repo. ", f: "dotsync mirrors your config files through a git repo, which keeps your machines in step. ", m: "sentence opens with an adverbial:" },
        { t: "Setup takes one command — no daemon, no account. ", f: "Setup takes one command, with no daemon and no account. ", m: "dash used as punctuation in" },
        { t: "Because it is plain git underneath, every change is reviewable and reversible. ", f: "Every change is reviewable and reversible, because it is plain git underneath. ", m: "sentence opens with an adverbial:" },
        { t: "Run it once on each machine and it stays out of your way." }
      ] }
  ];

  const RHYTHM = [
    { t: "Marta stood on the deck. The night was cold. The river was black. ", f: "Marta stood on the deck while the night turned cold and the river went black. " },
    { t: "She checked the rope. It was frayed. She checked the lights. They were dim. ", f: "She checked the rope and found it frayed, then checked the lights and found them dim. " },
    { t: "The ferry was old. She loved it anyway.", f: "The ferry was old and slow, and it smelled of diesel and wet canvas. She loved it anyway." }
  ];

  const QUIZ = [
    { text: "In the morning, the ferry leaves at six.", flag: true, why: "A prepositional phrase opens the sentence. Move it after the verb: the ferry leaves at six in the morning." },
    { text: "However, the ferry was late.", flag: false, why: "However is a conjunctive transition, so it is allowed as an opener." },
    { text: "To catch it, she ran for the dock.", flag: true, why: "An infinitive purpose phrase opens the sentence. Try: she ran for the dock to catch it." },
    { text: "Quietly, he closed the door behind him.", flag: true, why: "An -ly adverb opener. Put the subject first: he closed the door quietly behind him." },
    { text: "Instead, she walked home along the water.", flag: false, why: "A bare Instead is a transition and passes. Only Instead of ... counts as an adverbial." },
    { text: "The test passed — barely.", flag: true, why: "Rule 2. The em dash goes. A comma does the same job here." },
    { text: "Because the tide turned, they stayed another night.", flag: true, why: "A Because clause opens the sentence. Flip it: they stayed another night because the tide turned." },
    { text: "Meanwhile, the engine cooled in the dark.", flag: false, why: "Meanwhile is on the transition list, so it passes." }
  ];

  const STRIPES = "repeating-linear-gradient(135deg,var(--red) 0 4px,var(--badink) 4px 8px)";
  const wordCount = (t) => t.trim().split(/\s+/).filter(Boolean).length;
  const splitSentences = (t) => t.split(/(?<=[.!?])\s+/).map((x) => x.trim()).filter(Boolean);

  const state = { sample: 0, v: 0, playing: false, rv: 0, rplaying: false, qi: 0, ans: null, score: 0, dark: false };

  // Shared play loop: advances `key` by 1.4 every 50ms until it reaches 100.
  const timers = {};
  function play(key, playingKey, draw) {
    if (timers[key]) return;
    timers[key] = setInterval(() => {
      if (!state[playingKey]) { clearInterval(timers[key]); timers[key] = null; return; }
      state[key] = Math.min(100, state[key] + 1.4);
      if (state[key] >= 100) {
        clearInterval(timers[key]); timers[key] = null; state[playingKey] = false;
      }
      draw();
    }, 50);
  }

  function drawBars(container, bars, style) {
    container.replaceChildren(...bars.map((b) =>
      el("div", { style: `width:${style.w}px;height:${b.h}px;background:${b.bg};border-radius:3px 3px 0 0;${style.extra}` })));
  }

  function setStatus(dot, label, exit, count, wording) {
    dot.classList.toggle("ok", count === 0);
    label.textContent = wording;
    exit.textContent = count === 0 ? "0" : "1";
  }

  /* ---------- Examples ---------- */
  function drawDemo() {
    const cur = SAMPLES[state.sample];
    const v = state.v;
    const flagged = cur.segs.filter((s) => s.f !== undefined);
    const n = flagged.length;

    const out = [];
    const report = [];
    let origText = "";
    let fixed = 0;
    let k = 0;
    cur.segs.forEach((sg) => {
      const line = origText.split("\n").length;
      origText += sg.t;
      if (sg.f === undefined) { out.push(el("span", { class: "seg", text: sg.t })); return; }
      k += 1;
      const isFixed = v >= Math.round((k * 100) / n);
      if (isFixed) fixed += 1;
      out.push(el("span", { class: isFixed ? "seg seg-fixed" : "seg seg-bad", text: isFixed ? sg.f : sg.t }));
      if (!isFixed) {
        const t = sg.t.trim();
        report.push(el("li", { class: "mono", style: "font-size:12px;line-height:1.55;color:#EAE4D4" },
          el("span", { style: "color:#F0A39B", text: "✗" }), " ",
          el("span", { style: "color:#EAE4D4", text: `line ${line}: ${sg.m} "${t.slice(0, 52)}${t.length > 52 ? "…" : ""}"` })));
      }
    });
    const remaining = n - fixed;

    const A = [];
    const B = [];
    cur.segs.forEach((sg) => {
      if (!/[.!?]/.test(sg.t)) return;
      const isFlagged = sg.f !== undefined;
      const idx = isFlagged ? flagged.indexOf(sg) + 1 : 0;
      const isFixed = isFlagged && v >= Math.round((idx * 100) / n);
      const wo = wordCount(sg.t);
      const wn = wordCount(isFlagged && isFixed ? sg.f : sg.t);
      A.push({ h: Math.min(80, wo * 3 + 4), bg: isFlagged ? STRIPES : "var(--bar)" });
      B.push({ h: Math.min(80, wn * 3 + 4), w: wn, bg: !isFlagged ? "var(--ink)" : (isFixed ? "var(--green)" : STRIPES) });
    });

    $("intake").textContent = cur.intake;
    $("segs").replaceChildren(...out);
    $("vint").textContent = String(Math.round(v));
    $("slide").value = String(v);
    $("play").textContent = state.playing ? "Pause" : (v >= 100 ? "Replay" : "Play");
    $("report").replaceChildren(...report);
    setStatus($("dot"), $("status"), $("exit"), remaining,
      remaining === 0 ? "clean. no violations." : `The draft below breaks ${remaining} writing rule(s).`);
    drawBars($("barsA"), A, { w: 16, extra: "" });
    drawBars($("barsB"), B, { w: 16, extra: "transition:background .25s,height .25s;" });
    $("shortstat").textContent =
      `${remaining} of ${B.length} sentences flagged · ${B.filter((b) => b.w <= 6).length} at six words or fewer · longest ${B.reduce((m, b) => Math.max(m, b.w), 0)} words`;
  }

  function drawTabs() {
    $("tabs").replaceChildren(...SAMPLES.map((s, i) => {
      const on = i === state.sample;
      const b = el("button", { class: on ? "tab tab-on" : "tab", type: "button", "aria-pressed": String(on), text: s.label });
      b.addEventListener("click", () => {
        Object.assign(state, { sample: i, v: 0, playing: false });
        drawTabs();
        drawDemo();
      });
      return b;
    }));
  }

  /* ---------- Rhythm ---------- */
  function drawRhythm() {
    const rv = state.rv;
    let orig = "";
    let cur = "";
    const segs = RHYTHM.map((g, i) => {
      const done = rv >= Math.round(((i + 1) * 100) / RHYTHM.length);
      orig += g.t;
      cur += done ? g.f : g.t;
      return el("span", { class: done ? "seg seg-fixed" : "seg", text: done ? g.f : g.t });
    });
    const bars = (t) => splitSentences(t).map((x) => {
      const w = x.split(/\s+/).length;
      return { h: Math.min(80, w * 4 + 4), w };
    });
    const a = bars(orig);
    const b = bars(cur);

    $("rsegs").replaceChildren(...segs);
    $("rvint").textContent = String(Math.round(rv));
    $("slide2").value = String(rv);
    $("play2").textContent = state.rplaying ? "Pause" : (rv >= 100 ? "Replay" : "Play");
    drawBars($("rbarsA"), a.map((x) => ({ h: x.h, bg: "var(--bar)" })), { w: 20, extra: "" });
    drawBars($("rbarsB"), b.map((x) => ({ h: x.h, bg: "var(--ink)" })), { w: 20, extra: "transition:height .25s;" });
    $("rstat").textContent =
      `${b.filter((x) => x.w <= 6).length} of ${b.length} sentences at six words or fewer (${a.filter((x) => x.w <= 6).length} of ${a.length} originally) · longest ${b.reduce((m, x) => Math.max(m, x.w), 0)} words`;
  }

  /* ---------- Quiz ---------- */
  function drawQuiz() {
    const total = QUIZ.length;
    const done = state.qi >= total;
    const item = QUIZ[Math.min(state.qi, total - 1)];
    const answered = state.ans !== null;
    const right = answered && ((state.ans === "flag") === item.flag);

    $("q-active").hidden = done;
    $("q-done").hidden = !done;
    $("qprog").textContent = done ? "finished" : `sentence ${state.qi + 1} of ${total}`;
    $("q-text").textContent = item.text;
    $("q-answer").hidden = !answered;
    $("q-verdict").textContent = answered
      ? (right ? "Correct. The filter agrees." : `Not quite. The filter says ${item.flag ? "flag." : "pass."}`)
      : "";
    $("q-verdict").style.color = right ? "#D5EBDD" : "#F6D9D4";
    $("q-why").textContent = item.why;
    $("q-next").textContent = state.qi + 1 >= total ? "See your score" : "Next sentence";
    $("q-score").textContent = String(state.score);
    $("q-total").textContent = String(total);
  }

  function guess(answer) {
    if (state.ans) return;
    const item = QUIZ[state.qi];
    state.ans = answer;
    state.score += (answer === "flag") === item.flag ? 1 : 0;
    drawQuiz();
  }

  /* ---------- Live check ---------- */
  function drawCheck() {
    const violations = ProseFilter.check($("chk-src").value);
    $("chkReport").replaceChildren(...violations.map(([n, kind, msg]) => {
      const snip = (msg.match(/"([\s\S]*?)"\. /) || [0, msg])[1];
      return el("li", { class: "mono", style: "font-size:12px;line-height:1.55;color:#EAE4D4" },
        el("span", { style: "color:#F0A39B;font-weight:500", text: kind }), ` line ${n}: ${snip}`);
    }));
    const count = violations.length;
    setStatus($("chkdot"), $("chkstatus"), $("chkexit"), count,
      count === 0 ? "clean. no violations." : `${count} ${count === 1 ? "violation" : "violations"} found.`);
  }

  /* ---------- Light and dark ---------- */
  function drawMode() {
    $("pc").classList.toggle("dark", state.dark);
    const btn = $("mode");
    btn.setAttribute("aria-pressed", String(state.dark));
    btn.textContent = state.dark ? "Light mode" : "Dark mode";
  }

  /* ---------- Wiring ---------- */
  $("slide").addEventListener("input", (e) => { Object.assign(state, { v: Number(e.target.value), playing: false }); drawDemo(); });
  $("play").addEventListener("click", () => {
    if (state.playing) { state.playing = false; drawDemo(); return; }
    Object.assign(state, { playing: true, v: state.v >= 100 ? 0 : state.v });
    play("v", "playing", drawDemo);
    drawDemo();
  });
  $("slide2").addEventListener("input", (e) => { Object.assign(state, { rv: Number(e.target.value), rplaying: false }); drawRhythm(); });
  $("play2").addEventListener("click", () => {
    if (state.rplaying) { state.rplaying = false; drawRhythm(); return; }
    Object.assign(state, { rplaying: true, rv: state.rv >= 100 ? 0 : state.rv });
    play("rv", "rplaying", drawRhythm);
    drawRhythm();
  });
  $("q-flag").addEventListener("click", () => guess("flag"));
  $("q-pass").addEventListener("click", () => guess("pass"));
  $("q-next").addEventListener("click", () => { Object.assign(state, { qi: state.qi + 1, ans: null }); drawQuiz(); });
  $("q-restart").addEventListener("click", () => { Object.assign(state, { qi: 0, ans: null, score: 0 }); drawQuiz(); });
  $("chk-src").addEventListener("input", drawCheck);
  $("mode").addEventListener("click", () => {
    state.dark = !state.dark;
    try { localStorage.setItem("pc-mode", state.dark ? "dark" : "light"); } catch (_) { /* storage can be blocked */ }
    drawMode();
  });

  try { state.dark = localStorage.getItem("pc-mode") === "dark"; } catch (_) { /* storage can be blocked */ }
  if (!$("chk-src").value) $("chk-src").value = CHK_EXAMPLE;

  drawMode();
  drawTabs();
  drawDemo();
  drawRhythm();
  drawQuiz();
  drawCheck();
})();
