"""Marketing copy linguistic & stylometric analysis library.

Measures structural properties across marketing fields (headlines, subheads, CTAs,
feature descriptions, announcements) without flattening markdown headers or merging
unpunctuated headlines into subsequent text.
"""
import re
import statistics as st
import sys
from pathlib import Path

# Add skills/prose-craft/scripts to path to import prose_lib and stylo
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
    """Extract word tokens from text, preserving hyphenated terms."""
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", s)


def clean_headline(h):
    """Clean markdown formatting from headline while preserving exact wording and punctuation."""
    if not h:
        return ""
    # Strip markdown header prefix (# Headline)
    h = re.sub(r"^\s*#{1,6}\s+", "", h.strip())
    # Strip bold / italic formatting
    h = re.sub(r"[*_`]", "", h)
    return " ".join(h.split())


def classify_opener(s):
    """Classify the opening syntax of a sentence or headline.
    
    Returns one of:
      'adverbial': starts with preposition, adverbial clause, -ly adverb, or participle
      'imperative': starts with an action verb (implied 2nd person subject)
      'subject_first': starts with an overt subject pronoun, determiner, or named entity
      'noun_fragment': bare noun phrase without a finite verb
    """
    ws = words(s)
    if not ws:
        return "empty"
    
    # Check adverbial opener via prose_lib
    if pl.is_adverbial_opener(s):
        return "adverbial"
    
    first = ws[0].lower()
    
    # Check imperative verbs
    if first in COMMON_IMPERATIVES:
        return "imperative"
    
    # Check overt subject starters
    if first in SUBJECT_STARTERS:
        return "subject_first"
    
    # Check if there is a finite verb in the sentence
    # If the headline has no recognizable verb, it is a noun fragment
    has_verb = bool(re.search(r"\b(?:is|are|was|were|has|have|had|will|can|could|do|does|did|be|builds|helps|powers|scales|connects)\b", s, re.I))
    if not has_verb and len(ws) <= 6:
        return "noun_fragment"
        
    return "subject_first"


def headline_metrics(headline):
    """Analyze a single marketing headline accurately."""
    clean = clean_headline(headline)
    ws = words(clean)
    term_period = clean.endswith(".") and not clean.endswith("...")
    term_punct = clean[-1] if (clean and clean[-1] in ".!?") else ""
    
    return {
        "text": clean,
        "word_count": len(ws),
        "terminal_period": term_period,
        "terminal_punct": term_punct,
        "opener_type": classify_opener(clean),
        "has_emdash": bool(pl.DASH.search(headline)),
        "has_colon": ":" in headline,
    }


def buzzword_count(text):
    """Count occurrences of AI marketing clichés / intensifiers."""
    t_lower = text.lower()
    count = 0
    for b in BUZZWORDS:
        # Match word boundaries or exact hyphens
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
    
    hero = surface.get("hero", {})
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
        
    features = surface.get("features", [])
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
        
    ann = surface.get("announcement", {})
    if ann.get("body") or ann.get("title"):
        ann_text = f"{ann.get('title', '')} {ann.get('opener', '')} {ann.get('body', '')}".strip()
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
