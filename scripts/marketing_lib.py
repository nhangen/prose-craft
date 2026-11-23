"""Marketing copy linguistic & stylometric analysis library.

Measures structural properties across marketing fields (headlines, subheads, CTAs,
feature descriptions, announcements) without flattening markdown headers or merging
unpunctuated headlines into subsequent text.
"""
import re
import statistics as st
import sys
from pathlib import Path

# prose_lib and stylo ship inside the skill, not in this scripts/ directory.
SKILL_SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "prose-craft" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import prose_lib as pl
import stylo

BUZZWORDS = {
    "supercharge", "supercharged", "supercharges", "supercharging",
    "unleash", "unleashed", "unleashes", "unleashing",
    "delve", "delves", "delved", "delving",
    "seamless", "seamlessly",
    "game-changer", "game-changing", "gamechanger",
    "revolutionary", "revolutionize", "revolutionized", "revolutionizing",
    "elevate", "elevates", "elevated", "elevating",
    "next-level", "next level",
    "cutting-edge", "cutting edge",
    "effortless", "effortlessly",
    "streamline", "streamlined", "streamlines", "streamlining",
    "empower", "empowers", "empowered", "empowering",
    "transformative", "robust", "holistic",
    "harness", "harnesses", "harnessed", "harnessing",
    "unlock", "unlocks", "unlocked", "unlocking",
    "skyrocket", "skyrocketed", "skyrocketing",
    "beacon", "catalyst", "tapestry",
}

COMMON_IMPERATIVES = {
    "accept", "accelerate", "automate", "boost", "bring", "build", "collaborate",
    "connect", "create", "deliver", "deploy", "design", "discover", "drive",
    "empower", "enable", "engineer", "enjoy", "experience", "explore", "find",
    "generate", "get", "grow", "handle", "help", "implement", "integrate",
    "join", "launch", "lead", "manage", "meet", "move", "optimize", "orchestrate",
    "organize", "power", "protect", "reimagine", "run", "scale", "secure",
    "see", "send", "ship", "simplify", "start", "stop", "supercharge",
    "take", "track", "transform", "try", "unify", "unlock", "use", "work",
}

SUBJECT_STARTERS = {
    "the", "a", "an", "this", "that", "these", "those",
    "we", "you", "they", "it", "our", "your", "their", "its",
    "all", "every", "one", "no", "some",
}


def words(s):
    """Word tokens, including digits and accented letters; hyphenated terms stay whole."""
    return re.findall(r"[^\W_][\w'’‐‑-]*", s)


def clean_headline(h):
    """Clean markdown formatting from headline while preserving exact wording and punctuation."""
    if not h:
        return ""
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"^\s*#{1,6}\s+", "", h.strip())
    h = re.sub(r"[*_`]", "", h)
    return " ".join(h.split())


VERB = re.compile(r"\b(?:is|are|was|were|has|have|had|will|can|could|do|does|did|be|builds|helps|powers|scales|connects)\b", re.I)


def has_verb(s):
    return bool(VERB.search(s))


def is_fragment(segment, max_words=3):
    ws = words(segment)
    first = ws[0].lower()
    return (
        len(ws) <= max_words
        and first not in COMMON_IMPERATIVES
        and first not in SUBJECT_STARTERS
        and not has_verb(segment)
    )


def is_fragment_string(s):
    segments = [seg for seg in re.split(r"[.!?]+", s) if words(seg)]
    return len(segments) >= 2 and all(is_fragment(seg) for seg in segments)


def classify_opener(s):
    """Classify the opening syntax of a sentence or headline.

    Returns one of:
      'adverbial': starts with preposition, adverbial clause, -ly adverb, or participle
      'imperative': starts with an action verb (implied 2nd person subject)
      'subject_first': starts with an overt subject pronoun, determiner, or named entity
      'noun_fragment': bare noun phrase of six words or fewer without a finite verb
      'fragment_string': two or more short verbless segments (Fast. Simple. Powerful.)
      'unclassified': no recognized opener and no recognized verb
    """
    ws = words(s)
    if not ws:
        return "empty"
    if is_fragment_string(s):
        return "fragment_string"

    if pl.is_adverbial_opener(s):
        return "adverbial"

    first = ws[0].lower()

    if first in COMMON_IMPERATIVES:
        return "imperative"

    if first in SUBJECT_STARTERS:
        return "subject_first"

    if has_verb(s):
        return "subject_first"
    if len(ws) <= 6:
        return "noun_fragment"
    return "unclassified"


def headline_metrics(headline):
    """Analyze a single marketing headline accurately."""
    clean = clean_headline(headline)
    ws = words(clean)
    ellipsis = clean.endswith("...") or clean.endswith("\u2026")
    term_period = clean.endswith(".") and not ellipsis
    if ellipsis:
        term_punct = "\u2026"
    else:
        term_punct = clean[-1] if (clean and clean[-1] in ".!?") else ""

    budget = check_headline_budget(clean)
    dangling = check_dangling_line_endings(headline)

    return {
        "text": clean,
        "word_count": len(ws),
        "char_count": len(clean),
        "terminal_period": term_period,
        "terminal_punct": term_punct,
        "opener_type": classify_opener(clean),
        "has_emdash": bool(pl.DASH.search(headline)),
        "has_colon": ":" in headline,
        "budget_passes": budget["passes"],
        "dangling_line_breaks": len(dangling),
    }


DANGLING_CONNECTIVES = re.compile(
    r"\b(?:the|a|an|to|for|of|in|with|on|at|by|from|and|or|but|which)\s*$",
    re.IGNORECASE
)


def check_headline_budget(headline, max_words=7, max_chars=45):
    """Check whether a hero headline stays within the 2-line visual budget."""
    clean = clean_headline(headline)
    ws = words(clean)
    w_count = len(ws)
    c_count = len(clean)
    over_w = w_count > max_words
    over_c = c_count > max_chars
    return {
        "passes": not (over_w or over_c),
        "word_count": w_count,
        "char_count": c_count,
        "over_words": over_w,
        "over_chars": over_c,
    }


def check_dangling_line_endings(text):
    """Detect lines ending with stranded weak connectives in explicitly broken copy.

    Only analyzes text containing explicit newlines or <br> tags.
    """
    normalized = re.sub(r"(?i)<br\s*/?>", "\n", text)
    lines = [(i, line.strip()) for i, line in enumerate(normalized.splitlines(), 1) if line.strip()]
    if len(lines) <= 1:
        return []

    violations = []
    for i, line in lines[:-1]:
        clean_line = clean_headline(line)
        tokens = words(clean_line)
        m = DANGLING_CONNECTIVES.fullmatch(tokens[-1]) if tokens and clean_line.endswith(tokens[-1]) else None
        if m:
            violations.append({
                "line_number": i,
                "line": line,
                "dangling_word": m.group(0).strip(),
            })
    return violations


def check_orphan_tail(text):
    """Check if the final line of multi-line text is an isolated single word (<8 chars)."""
    normalized = re.sub(r"(?i)<br\s*/?>", "\n", text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    if len(lines) <= 1:
        return False
    last_line = lines[-1]
    ws = words(last_line)
    return len(ws) == 1 and len(last_line) < 8


def buzzword_count(text):
    """Count occurrences of AI marketing clichés / intensifiers."""
    t_lower = text.lower()
    count = 0
    for b in BUZZWORDS:
        pattern = r"\b" + re.escape(b) + r"\b"
        count += len(re.findall(pattern, t_lower))
    return count


def surface_metrics(surface):
    """Extract metrics from a structured surface entry:
    {
      'surface_type': 'home'|'product'|'pricing'|'launch',
      'hero': {'headline': '...', 'subhead': '...', 'cta': '...'},
      'features': [{'header': '...', 'description': '...'}],
      'announcement': {'title': '...', 'opener': '...', 'body': '...'}
    }
    """
    res = {}

    hero = surface.get("hero") or {}
    if hero.get("headline"):
        res["hero_headline"] = headline_metrics(hero["headline"])
    if hero.get("subhead"):
        sub_text = hero["subhead"].strip()
        sub_ws = words(sub_text)
        sub_sents = stylo.sentences(sub_text)
        res["hero_subhead"] = {
            "text": sub_text,
            "word_count": len(sub_ws),
            "sentence_count": len(sub_sents),
            "has_emdash": bool(pl.DASH.search(sub_text)),
            "opener_type": classify_opener(sub_text),
            "buzzwords": buzzword_count(sub_text),
        }
    if hero.get("cta"):
        cta_text = hero["cta"].strip()
        res["hero_cta"] = {
            "text": cta_text,
            "word_count": len(words(cta_text)),
            "opener_type": classify_opener(cta_text),
            "buzzwords": buzzword_count(cta_text),
        }

    features = [f for f in (surface.get("features") or []) if isinstance(f, dict)]
    if features:
        feat_headers = [f.get("header", "") for f in features if f.get("header")]
        feat_descs = [f.get("description", "") for f in features if f.get("description")]
        res["features"] = {
            "count": len(features),
            "header_word_counts": [len(words(h)) for h in feat_headers],
            "desc_word_counts": [len(words(d)) for d in feat_descs],
            "desc_emdash_count": sum(bool(pl.DASH.search(d)) for d in feat_descs),
            "desc_buzzwords": sum(buzzword_count(d) for d in feat_descs),
        }

    ann = surface.get("announcement") or {}
    if ann.get("body") or ann.get("title"):
        ann_text = " ".join(ann.get(k) or "" for k in ("title", "opener", "body")).strip()
        ann_ws = words(ann_text)
        ann_sents = stylo.sentences(ann_text)
        lens = [len(words(s)) for s in ann_sents if words(s)]
        res["announcement"] = {
            "word_count": len(ann_ws),
            "sentence_count": len(ann_sents),
            "mean_sentence_length": st.mean(lens) if lens else 0.0,
            "emdash_count": len(pl.DASH.findall(ann_text)),
            "buzzwords": buzzword_count(ann_text),
            "adverbial_opener_share": pl.adverbial_opener_share(ann_text),
        }

    return res
