#!/usr/bin/env python3
"""Sentence-level stylometrics: guardrails and error-analysis aids, never a quality score.

Usage:
  stylo.py samples <dir>...        one row per generated sample, grouped by register
  stylo.py windows <text>...       random 300-word windows from reference texts

Run with `python3 -I` when reading downloaded text.
"""
import json, random, re, statistics as st, sys
from pathlib import Path

ABBR = re.compile(r"\b(Mr|Mrs|Ms|Dr|St|Mme|M|Capt|Col|Gen|Lt|Sr|Jr|vs|etc)\.$")
SPLIT = re.compile(r"(?<=[.!?])[\"'”’)]*\s+(?=[\"'“‘(]?[A-Z])")


def clean(t):
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"(?m)^\s*#{1,6}\s.*$", " ", t)
    t = re.sub(r"(?m)^\s*\*\*[A-Za-z .'-]{1,24}:\*\*", " ", t)
    t = re.sub(r"[*_`>]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def sentences(t):
    out, buf = [], ""
    for part in SPLIT.split(t):
        buf = (buf + " " + part).strip() if buf else part
        if ABBR.search(buf):
            continue
        out.append(buf)
        buf = ""
    if buf:
        out.append(buf)
    return out


def words(s):
    return re.findall(r"[A-Za-z][A-Za-z'’-]*", s)


def mattr(ws, w=50):
    ws = [x.lower() for x in ws]
    if len(ws) < w:
        return float("nan")
    return st.mean(len(set(ws[i:i + w])) / w for i in range(0, len(ws) - w + 1, 10))


def feats(text):
    t = clean(text)
    ss = [s for s in sentences(t) if words(s)]
    ls = [len(words(s)) for s in ss]
    ws = words(t)
    n = max(len(ws), 1)
    k = lambda p: 1000 * len(re.findall(p, t)) / n
    firsts = [words(s)[0].lower() for s in ss]
    mean = st.mean(ls) if ls else float("nan")
    return {
        "words": len(ws), "sents": len(ss), "len_mean": mean,
        "len_cv": (st.pstdev(ls) / mean) if len(ls) > 1 else float("nan"),
        "p90": sorted(ls)[int(0.9 * (len(ls) - 1))] if ls else float("nan"),
        "short_le6": sum(x <= 6 for x in ls) / max(len(ls), 1),
        "long_ge30": sum(x >= 30 for x in ls) / max(len(ls), 1),
        "open_uniq": len(set(firsts)) / max(len(firsts), 1),
        "open_the_pron": sum(f in {"the", "he", "she", "it", "they", "i", "we", "you"} for f in firsts) / max(len(firsts), 1),
        "semi_k": k(r";"), "colon_k": k(r":"), "paren_k": k(r"\("), "q_k": k(r"\?"),
        "comma_per_sent": t.count(",") / max(len(ss), 1),
        "passive_k": k(r"\b(?:was|were|is|are|been|being|be)\s+\w+(?:ed|en)\b"),
        "mattr50": mattr(ws), "wordlen": st.mean(len(w) for w in ws) if ws else float("nan"),
    }


def table(rows):
    keys = [k for k in next(iter(rows.values()))[0] if k not in ("words", "sents")]
    print("group".ljust(16), "n".rjust(3), " ".join(k[:10].rjust(10) for k in keys))
    for g, fs in sorted(rows.items()):
        vals = [st.mean([f[k] for f in fs if f[k] == f[k]] or [float('nan')]) for k in keys]
        print(g.ljust(16), str(len(fs)).rjust(3), " ".join(f"{v:10.2f}" for v in vals))


def main():
    mode, args = sys.argv[1], sys.argv[2:]
    rows = {}
    if mode == "samples":
        for d in args:
            for p in sorted(Path(d).glob("*.txt")):
                reg = p.name.split(".")[0].rsplit("-", 1)[0]
                rows.setdefault(f"{Path(d).name}:{reg}", []).append(feats(p.read_text()))
    elif mode == "windows":
        rnd = random.Random(7)
        for p in args:
            ws = clean(Path(p).read_text()).split()
            mid = ws[len(ws) // 10: -len(ws) // 10]
            for _ in range(40):
                i = rnd.randrange(0, len(mid) - 300)
                rows.setdefault(Path(p).stem, []).append(feats(" ".join(mid[i:i + 300])))
    table(rows)


if __name__ == "__main__":
    main()
