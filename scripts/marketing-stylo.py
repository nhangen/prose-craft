#!/usr/bin/env python3
"""CLI stylometrics tool for marketing copy datasets.

Analyzes marketing corpus JSON fixtures and outputs field-aware comparative
statistics across brands and categories without flattening headlines.

Usage:
  marketing-stylo.py analyze <corpus.json>...
  marketing-stylo.py compare <human_corpus.json> <llm_baseline.json>
"""
import argparse
import json
import statistics as st
import sys
from pathlib import Path

# Ensure scripts dir is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import marketing_lib as ml


def load_corpus(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        sys.exit(f"{path}: {e}")
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "companies" in data:
        return data["companies"]
    if isinstance(data, dict) and "surfaces" in data:
        return [data]
    sys.exit(f"{path}: expected a list of companies, {{'companies': [...]}}, or one company with 'surfaces'")


def require_headlines(label, metrics):
    if metrics["headline_count"] == 0:
        sys.exit(f"{label}: no headlines found, so there is nothing to measure")


def pool_metrics(companies):
    headlines = []
    subheads = []
    ctas = []
    emdash_headlines = 0
    emdash_subheads = 0
    period_headlines = 0
    total_buzzwords = 0
    total_words = 0
    opener_counts = {"imperative": 0, "subject_first": 0, "noun_fragment": 0, "adverbial": 0, "empty": 0}

    for comp in companies:
        for surf in comp.get("surfaces", []):
            m = ml.surface_metrics(surf)
            hh = m.get("hero_headline")
            if hh:
                headlines.append(hh["word_count"])
                if hh["has_emdash"]:
                    emdash_headlines += 1
                if hh["terminal_period"]:
                    period_headlines += 1
                op = hh.get("opener_type", "empty")
                opener_counts[op] = opener_counts.get(op, 0) + 1
                total_words += hh["word_count"]
                total_buzzwords += ml.buzzword_count(hh["text"])
                
            hs = m.get("hero_subhead")
            if hs:
                subheads.append(hs["word_count"])
                if hs["has_emdash"]:
                    emdash_subheads += 1
                total_words += hs["word_count"]
                total_buzzwords += hs["buzzwords"]
                
            hc = m.get("hero_cta")
            if hc:
                ctas.append(hc["word_count"])
                total_words += hc["word_count"]
                total_buzzwords += hc["buzzwords"]

            feats = m.get("features")
            if feats:
                total_words += sum(feats.get("desc_word_counts", []))
                total_buzzwords += feats.get("desc_buzzwords", 0)

            ann = m.get("announcement")
            if ann:
                total_words += ann.get("word_count", 0)
                total_buzzwords += ann.get("buzzwords", 0)

    n_h = max(len(headlines), 1)
    n_s = max(len(subheads), 1)
    
    return {
        "companies_count": len(companies),
        "headline_count": len(headlines),
        "headline_len_mean": st.mean(headlines) if headlines else 0.0,
        "headline_len_p90": sorted(headlines)[int(0.9 * (len(headlines) - 1))] if headlines else 0,
        "headline_len_min": min(headlines) if headlines else 0,
        "headline_len_max": max(headlines) if headlines else 0,
        "headline_period_rate": period_headlines / n_h,
        "headline_emdash_rate": emdash_headlines / n_h,
        "subhead_len_mean": st.mean(subheads) if subheads else 0.0,
        "subhead_emdash_rate": emdash_subheads / n_s,
        "cta_len_mean": st.mean(ctas) if ctas else 0.0,
        "opener_dist": {k: round(v / n_h, 3) for k, v in opener_counts.items() if k != "empty"},
        "buzzwords_per_1k": (1000.0 * total_buzzwords / max(total_words, 1)),
    }


def print_summary_table(title, metrics):
    print(f"\n=== {title} ===")
    print(f"Companies: {metrics['companies_count']} | Headlines Analyzed: {metrics['headline_count']}")
    print(f"Headline Length (words): Mean={metrics['headline_len_mean']:.1f}, Min={metrics['headline_len_min']}, Max={metrics['headline_len_max']}, P90={metrics['headline_len_p90']}")
    print(f"Subhead Length (words):  Mean={metrics['subhead_len_mean']:.1f}")
    print(f"CTA Length (words):      Mean={metrics['cta_len_mean']:.1f}")
    print(f"Headline Period Rate:   {metrics['headline_period_rate']*100:.1f}%")
    print(f"Headline Em-Dash Rate:  {metrics['headline_emdash_rate']*100:.1f}%")
    print(f"Subhead Em-Dash Rate:   {metrics['subhead_emdash_rate']*100:.1f}%")
    print(f"Buzzword Rate (/1k w):  {metrics['buzzwords_per_1k']:.2f}")
    print("Headline Opener Distribution:")
    for op, rate in sorted(metrics['opener_dist'].items(), key=lambda x: -x[1]):
        print(f"  - {op.ljust(16)}: {rate*100:5.1f}%")


def compare_corpora(human_path, llm_path):
    h_data = load_corpus(human_path)
    l_data = load_corpus(llm_path)
    
    h_met = pool_metrics(h_data)
    l_met = pool_metrics(l_data)
    require_headlines(human_path, h_met)
    require_headlines(llm_path, l_met)
    
    print_summary_table(f"HUMAN BENCHMARK ({Path(human_path).stem})", h_met)
    print_summary_table(f"LLM BASELINE ({Path(llm_path).stem})", l_met)
    
    print("\n=== KEY DIVERGENCES (Human vs. LLM) ===")
    print(f"Headline Word Count:   Human {h_met['headline_len_mean']:.1f} vs LLM {l_met['headline_len_mean']:.1f} (Delta: {l_met['headline_len_mean'] - h_met['headline_len_mean']:+.1f})")
    print(f"Subhead Word Count:    Human {h_met['subhead_len_mean']:.1f} vs LLM {l_met['subhead_len_mean']:.1f} (Delta: {l_met['subhead_len_mean'] - h_met['subhead_len_mean']:+.1f})")
    print(f"Headline Em-Dash Rate: Human {h_met['headline_emdash_rate']*100:.1f}% vs LLM {l_met['headline_emdash_rate']*100:.1f}%")
    print(f"Subhead Em-Dash Rate:  Human {h_met['subhead_emdash_rate']*100:.1f}% vs LLM {l_met['subhead_emdash_rate']*100:.1f}%")
    print(f"Buzzword Rate (/1k w): Human {h_met['buzzwords_per_1k']:.2f} vs LLM {l_met['buzzwords_per_1k']:.2f} (Delta: {l_met['buzzwords_per_1k'] - h_met['buzzwords_per_1k']:+.2f})")
    print(f"Adverbial Opener Share:Human {h_met['opener_dist'].get('adverbial', 0)*100:.1f}% vs LLM {l_met['opener_dist'].get('adverbial', 0)*100:.1f}%")


def main():
    p = argparse.ArgumentParser(description="Marketing Copy Stylometrics Tool")
    sub = p.add_subparsers(dest="cmd", required=True)
    
    a_cmd = sub.add_parser("analyze")
    a_cmd.add_argument("file", help="Path to corpus JSON")
    
    c_cmd = sub.add_parser("compare")
    c_cmd.add_argument("human", help="Path to human benchmark JSON")
    c_cmd.add_argument("llm", help="Path to LLM baseline JSON")
    
    args = p.parse_args()
    if args.cmd == "analyze":
        data = load_corpus(args.file)
        metrics = pool_metrics(data)
        require_headlines(args.file, metrics)
        print_summary_table(f"Corpus: {Path(args.file).name}", metrics)
    elif args.cmd == "compare":
        compare_corpora(args.human, args.llm)


if __name__ == "__main__":
    main()
