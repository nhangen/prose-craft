#!/usr/bin/env python3
"""Reject prose that contains an em dash or a spaced hyphen used as a dash.

Usage: reject-emdash.py FILE... | reject-emdash.py - < text
Exit 0 clean, 1 at least one hit, 2 usage or read error.
"""
import sys

import prose_lib as pl


def hits(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in pl.DASH.finditer(line):
            out.append((n, m.start() + 1, line.strip()[:80]))
    return out


def main(argv):
    if not argv:
        print("usage: reject-emdash.py FILE... | -", file=sys.stderr)
        return 2
    bad = 0
    for name in argv:
        try:
            text = sys.stdin.read() if name == "-" else open(name, encoding="utf-8").read()
        except (OSError, UnicodeError) as e:
            detail = e.strerror if isinstance(e, OSError) else str(e)
            print(f"error: {name}: {detail}", file=sys.stderr)
            return 2
        for n, col, ctx in hits(text):
            print(f"{'stdin' if name == '-' else name}:{n}:{col}: dash as punctuation: {ctx}")
            bad += 1
    if bad:
        print(f"rejected: {bad} dash(es). Use a period, comma, colon or parentheses.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
