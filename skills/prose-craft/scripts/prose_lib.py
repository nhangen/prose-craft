"""Guardrail measurements for prose-craft rounds. Guardrails catch regressions; they are never a quality score."""
import re
import statistics as st

import stylo

TRAILER = re.compile(r"(?mi)^\s*(co-authored-by|claude-session|signed-off-by):.*$")
META = re.compile(
    r"(?mi)^\s*[*_>\-]*\s*(?:notes?\s*:|a few notes\b|a note on\b|word count\s*:|here(?:'s| is) (?:a|the) (?:brief )?(?:note|explanation))"
)
NEGPAR = re.compile(
    r"\b(?:isn't|is not|aren't|are not|wasn't|weren't|not)\b[^.!?\n]{0,60}[.;,]\s*(?:it's|it is|that's|they're|but|instead)\b",
    re.I,
)
DASH = re.compile(r"\u2014|(?<=\S) - (?=\S)")
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
CAPS = re.compile(r"\b[A-Z][a-zA-Z'’-]+")
STARTERS = {"The", "A", "An", "On", "In", "At", "It", "He", "She", "They", "We", "I", "You", "This", "That",
            "There", "When", "But", "And", "So", "As", "By", "For", "Of", "To", "If", "Then", "His", "Her", "Their"}


OPENER_PREPS = {
    "in", "on", "at", "by", "with", "from", "for", "under", "after", "before", "during", "since", "without",
    "because", "when", "while", "if", "although", "though", "as", "once", "given", "over", "between", "across",
    "within", "through", "per", "to", "upon", "into", "among", "beyond", "despite", "throughout", "until",
    "unless", "whenever",
}
CLAUSE_OPENERS = {"where", "wherever"}
NOT_PARTICIPLES = {"nothing", "something", "anything", "everything", "morning", "evening", "king", "thing",
                   "ring", "spring", "string", "wing", "ceiling", "building", "meaning", "feeling", "ending"}
CONJUNCTIVE = {"furthermore", "additionally", "moreover", "however", "therefore", "thus", "also", "instead",
               "then", "still", "finally", "meanwhile", "similarly", "likewise", "nevertheless", "nonetheless"}


def is_adverbial_opener(sentence):
    ws = re.findall(r"[A-Za-z][A-Za-z'’-]*", sentence)
    if not ws:
        return False
    first = ws[0].lower()
    if first == "instead":
        return len(ws) > 1 and ws[1].lower() == "of"
    if first in CONJUNCTIVE:
        return False
    if first in OPENER_PREPS:
        return True
    lead = sentence[: sentence.find(ws[min(len(ws) - 1, 9)])]
    if first in CLAUSE_OPENERS:
        return "," in sentence
    if first.endswith("ly") and len(first) > 3:
        return sentence.lstrip().lower().startswith(first + ",")
    return first.endswith("ing") and first not in NOT_PARTICIPLES and "," in lead


def adverbial_opener_share(text):
    ss = [s for s in stylo.sentences(stylo.clean(text)) if re.search(r"[A-Za-z]", s)]
    return sum(is_adverbial_opener(s) for s in ss) / len(ss) if ss else 0.0


def normalize(text):
    t = text.strip()
    if t.startswith("```") and t.endswith("```") and t.count("```") == 2:
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t[: t.rfind("```")]
    t = TRAILER.sub("", t)
    return t.strip()


def has_meta_note(text):
    return bool(META.search(text))


def negative_parallelism(text):
    return bool(NEGPAR.search(text))


def _bare_words(text):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", stylo.clean(re.sub(r"[*_`]", "", text)))


def markdown_density(text):
    heads = len(re.findall(r"(?m)^\s*#{1,6}\s", text))
    bolds = len(re.findall(r"\*\*[^*\n]+\*\*", text))
    n = max(len(re.findall(r"[A-Za-z][A-Za-z'’-]*", re.sub(r"[*#_`]", " ", text))), 1)
    return 100.0 * (heads + bolds) / n


def _nums(s):
    return {m.group(0).replace(",", "").rstrip(".") for m in NUM.finditer(s)}


def unsupplied_numbers(prompt, text):
    given = _nums(prompt)
    return sorted(_nums(text) - given)


def _title(t):
    first = t.strip().split("\n", 1)[0]
    return re.sub(r"^#+\s*", "", first).lower().strip() if first.startswith("#") else None


def _body(t):
    lines = [l for l in t.strip().split("\n")]
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    return " ".join(lines).strip()


def _names(t):
    return {w for w in CAPS.findall(t) if w not in STARTERS}


def _pair(a, b):
    parts = []
    ta, tb = _title(a), _title(b)
    if ta and tb:
        parts.append(1.0 if ta == tb else 0.0)
    oa, ob = _body(a).lower().split()[:4], _body(b).lower().split()[:4]
    parts.append(1.0 if oa == ob else 0.0)
    na, nb = _names(a), _names(b)
    parts.append(len(na & nb) / len(na | nb) if na | nb else 0.0)
    return st.mean(parts)


def convergence(texts):
    if len(texts) < 2:
        return 0.0
    pairs = [_pair(texts[i], texts[j]) for i in range(len(texts)) for j in range(i + 1, len(texts))]
    return st.mean(pairs)


def sample_metrics(prompt, raw):
    t = normalize(raw)
    f = stylo.feats(t)
    ok = lambda v: v if v == v else None
    return {
        "fragment_share": ok(f["short_le6"]),
        "pronoun_opener_share": ok(f["open_the_pron"]),
        "markdown_density": markdown_density(t),
        "adverbial_opener_share": adverbial_opener_share(t),
        "emdash_count": float(len(DASH.findall(t))),
        "meta_note_rate": 1.0 if has_meta_note(raw) else 0.0,
        "negparallel_rate": 1.0 if negative_parallelism(t) else 0.0,
        "unsupplied_numbers": float(len(unsupplied_numbers(prompt, t))),
    }


def mean_of(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(st.mean(vals), 4) if vals else 0.0


def se_of(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(st.stdev(vals) / len(vals) ** 0.5, 4) if len(vals) > 1 else 0.0
