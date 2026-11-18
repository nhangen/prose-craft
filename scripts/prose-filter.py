#!/usr/bin/env python3
"""Deterministic prose filter for output from any agent.

  prose-filter.py check [FILE|-]
      Exit 0 clean, 1 violations (a correction message goes to stdout), 2 usage or read error.
  prose-filter.py run --agent CMD [--max-rounds N] [FILE|-]
      Feed the draft back to the agent until it passes. CMD receives the correction message on
      stdin and prints the corrected text on stdout (for example `claude -p`, `codex exec -`,
      `opencode run`, `ollama run MODEL`). Clean text goes to stdout, exit 0. Exit 1 if the
      draft still fails after N rounds, 2 if the agent command fails.

Rules, all mechanical: no em dash or spaced hyphen as punctuation; no sentence opens with an adverbial.
Fenced code and inline code are skipped.
"""
import argparse
import re
import shlex
import subprocess
import sys

import prose_lib as pl
import stylo

RULES = ("1. No em dash and no spaced hyphen as punctuation. Use a period, comma, colon or parentheses.\n"
         "2. No sentence opens with an adverbial (a prepositional phrase, an infinitive purpose phrase, a Because, When or If "
         "clause, a participial phrase, or an -ly adverb). Move the phrase after the verb. Furthermore, Additionally, "
         "Moreover, However, Therefore, Thus, Also, Then, Still, Finally, Meanwhile are fine.")
ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


def mask_code(text):
    text = re.sub(r"```.*?```", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "Code", text)


def paragraphs(text):
    cur, start = [], 0
    for n, line in enumerate(text.splitlines(), 1):
        starts_new = not line.strip() or ITEM.match(line) or line.lstrip().startswith("#")
        if starts_new and cur:
            yield start, " ".join(cur)
            cur = []
        if line.strip():
            if not cur:
                start = n
            cur.append(ITEM.sub("", line).strip())
    if cur:
        yield start, " ".join(cur)


def check(text):
    masked = mask_code(text)
    out = []
    for n, line in enumerate(masked.splitlines(), 1):
        for m in pl.DASH.finditer(line):
            ctx = line.strip()[:80]
            out.append((n, "dash", f'dash used as punctuation in "{ctx}". Use a period, comma, colon or parentheses.'))
            break
    for n, para in paragraphs(masked):
        for s in stylo.sentences(re.sub(r"[*_]", "", para)):
            if re.search(r"[A-Za-z]", s) and pl.is_adverbial_opener(s):
                out.append((n, "opener", f'sentence opens with an adverbial: "{s[:70]}". Put the subject first and move the phrase after the verb.'))
    return sorted(out)


def feedback(text, violations):
    lines = "\n".join(f"- line {n}: {msg}" for n, _, msg in violations)
    return (f"The draft below breaks {len(violations)} writing rule(s).\n\nRULES\n{RULES}\n\nVIOLATIONS\n{lines}\n\n"
            "Fix every violation by editing only the flagged sentences. Keep every fact, number and name. "
            "Return only the corrected text, with no commentary and no code fence.\n\nDRAFT\n" + text)


def read(name):
    return sys.stdin.read() if name == "-" else open(name, encoding="utf-8").read()


def main(argv):
    ap = argparse.ArgumentParser(prog="prose-filter.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("file", nargs="?", default="-")
    r = sub.add_parser("run")
    r.add_argument("--agent", required=True)
    r.add_argument("--max-rounds", type=int, default=3)
    r.add_argument("file", nargs="?", default="-")
    a = ap.parse_args(argv)
    try:
        text = read(a.file)
    except (OSError, UnicodeError) as e:
        detail = e.strerror if isinstance(e, OSError) else str(e)
        print(f"error: {a.file}: {detail}", file=sys.stderr)
        return 2
    v = check(text)
    if a.cmd == "check":
        if v:
            print(feedback(text, v))
            return 1
        return 0
    if a.max_rounds <= 0:
        print("error: --max-rounds must be a positive integer", file=sys.stderr)
        return 2
    try:
        argv_agent = shlex.split(a.agent)
    except ValueError as e:
        print(f"error: invalid --agent command: {e}", file=sys.stderr)
        return 2
    if not argv_agent:
        print("error: --agent command is empty", file=sys.stderr)
        return 2
    for rnd in range(a.max_rounds):
        if not v:
            sys.stdout.write(text if text.endswith("\n") else text + "\n")
            return 0
        try:
            res = subprocess.run(argv_agent, input=feedback(text, v), capture_output=True, text=True)
        except (OSError, UnicodeError) as e:
            print(f"error: could not run agent command: {e}", file=sys.stderr)
            return 2
        if res.returncode != 0 or not res.stdout.strip():
            print(f"error: agent failed in round {rnd + 1} (exit {res.returncode}): {res.stderr.strip()[:200]}", file=sys.stderr)
            return 2
        text = pl.normalize(res.stdout)
        if not text.strip():
            print(f"error: agent returned empty text in round {rnd + 1}", file=sys.stderr)
            return 2
        v = check(text)
    if not v:
        sys.stdout.write(text + "\n")
        return 0
    print(f"rejected after {a.max_rounds} rounds, {len(v)} violation(s) remain:", file=sys.stderr)
    for n, _, msg in v:
        print(f"- line {n}: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
