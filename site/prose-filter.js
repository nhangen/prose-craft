const ProseFilter = (() => {
  const DASH = /—|(?<=\S) - (?=\S)/;
  const ITEM = /^\s*(?:[-*+]|\d+[.)])\s+/;
  const ABBR = /\b(Mr|Mrs|Ms|Dr|St|Mme|M|Capt|Col|Gen|Lt|Sr|Jr|vs|etc)\.$/;
  const SPLIT = /(?<=[.!?])["'”’)]*\s+(?=["'“‘(]?[A-Z])/;
  const LINE_BREAK = /\r\n|[\n\r\v\f\x1c-\x1e\u0085\u2028\u2029]/;
  const OPENER_PREPS = new Set([
    "in", "on", "at", "by", "with", "from", "for", "under", "after", "before", "during", "since", "without",
    "because", "when", "while", "if", "although", "though", "as", "once", "given", "over", "between", "across",
    "within", "through", "per", "to", "upon", "into", "among", "beyond", "despite", "throughout", "until",
    "unless", "whenever",
  ]);
  const CLAUSE_OPENERS = new Set(["where", "wherever"]);
  const CONJUNCTIVE = new Set(["furthermore", "additionally", "moreover", "however", "therefore", "thus", "also",
    "instead", "then", "still", "finally", "meanwhile", "similarly", "likewise", "nevertheless", "nonetheless"]);
  const NOT_PARTICIPLES = new Set(["nothing", "something", "anything", "everything", "morning", "evening", "king",
    "thing", "ring", "spring", "string", "wing", "ceiling", "building", "meaning", "feeling", "ending",
    "marketing", "engineering", "accounting", "advertising", "publishing", "programming"]);

  const RULES = "1. No em dash and no spaced hyphen as punctuation. Use a period, comma, colon or parentheses.\n" +
    "2. No sentence opens with an adverbial (a prepositional phrase, an infinitive purpose phrase, a Because, When or If " +
    "clause, a participial phrase, or an -ly adverb). Move the phrase after the verb. Furthermore, Additionally, " +
    "Moreover, However, Therefore, Thus, Also, Then, Still, Finally, Meanwhile are fine.";

  const cut = (s, n) => Array.from(s).slice(0, n).join("");
  const words = (s) => s.match(/[A-Za-z][A-Za-z'’-]*/g) || [];

  function isAdverbialOpener(sentence) {
    const ws = words(sentence);
    if (!ws.length) return false;
    const first = ws[0].toLowerCase();
    if (first === "instead") return ws.length > 1 && ws[1].toLowerCase() === "of";
    if (CONJUNCTIVE.has(first)) return false;
    if (OPENER_PREPS.has(first)) return true;
    const lead = sentence.slice(0, sentence.indexOf(ws[Math.min(ws.length - 1, 9)]));
    if (CLAUSE_OPENERS.has(first)) return sentence.includes(",");
    if (first.endsWith("ly") && first.length > 3) return sentence.trimStart().toLowerCase().startsWith(first + ",");
    return first.endsWith("ing") && !NOT_PARTICIPLES.has(first) && lead.includes(",");
  }

  function* sentenceRanges(text) {
    let start = 0;
    for (const match of text.matchAll(new RegExp(SPLIT, "g"))) {
      const sentence = text.slice(start, match.index);
      if (ABBR.test(sentence)) continue;
      const next = match.index + match[0].length;
      yield [sentence, text.slice(start, next)];
      start = next;
    }
    yield [text.slice(start), ""];
  }

  function sentences(text) {
    return Array.from(sentenceRanges(text), ([sentence]) => sentence);
  }

  function maskCode(text) {
    text = text.replace(/```[\s\S]*?```/g, (m) => m.replace(/[^\n]/g, " "));
    return text.replace(/`[^`\n]*`/g, "Code");
  }

  function paragraphs(text) {
    const out = [];
    let cur = [];
    let start = 0;
    const lines = text.split(LINE_BREAK);
    if (lines.length && lines[lines.length - 1] === "") lines.pop();
    lines.forEach((line, i) => {
      const n = i + 1;
      const startsNew = !line.trim() || ITEM.test(line) || line.trimStart().startsWith("#");
      if (startsNew && cur.length) {
        out.push([start, cur.join("\n")]);
        cur = [];
      }
      if (line.trim()) {
        if (!cur.length) start = n;
        cur.push(line.replace(ITEM, "").trim());
        if (line.trimStart().startsWith("#")) {
          out.push([start, cur[0]]);
          cur = [];
        }
      }
    });
    if (cur.length) out.push([start, cur.join("\n")]);
    return out;
  }

  function check(text) {
    const masked = maskCode(text);
    const out = [];
    const lines = masked.split(LINE_BREAK);
    if (lines.length && lines[lines.length - 1] === "") lines.pop();
    lines.forEach((line, i) => {
      if (DASH.test(line)) {
        const ctx = cut(line.trim(), 80);
        out.push([i + 1, "dash", `dash used as punctuation in "${ctx}". Use a period, comma, colon or parentheses.`]);
      }
    });
    for (const [n, para] of paragraphs(masked)) {
      let line = n;
      for (const [source, consumed] of sentenceRanges(para.replace(/[*_]/g, ""))) {
        const s = source.replace(/\n/g, " ");
        if (/[A-Za-z]/.test(s) && isAdverbialOpener(s)) {
          out.push([line, "opener", `sentence opens with an adverbial: "${cut(s, 70)}". Put the subject first and move the phrase after the verb.`]);
        }
        line += consumed.split("\n").length - 1;
      }
    }
    const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
    out.sort((a, b) => cmp(a[0], b[0]) || cmp(a[1], b[1]) || cmp(a[2], b[2]));
    return out;
  }

  function feedback(text, violations) {
    const lines = violations.map(([n, , msg]) => `- line ${n}: ${msg}`).join("\n");
    return `The draft below breaks ${violations.length} writing rule(s).\n\nRULES\n${RULES}\n\nVIOLATIONS\n${lines}\n\n` +
      "Fix every violation by editing only the flagged sentences. Keep every fact, number and name. " +
      "Return only the corrected text, with no commentary and no code fence.\n\nDRAFT\n" + text;
  }

  return { check, feedback, isAdverbialOpener, sentences, RULES };
})();
if (typeof module !== "undefined") module.exports = ProseFilter;
