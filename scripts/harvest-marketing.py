#!/usr/bin/env python3
"""Harvester and snapshot manager for the 31-brand marketing copy corpus.

Maintains curated marketing copy snapshots across 5 surfaces per brand:
- Home: Main landing hero & value propositions
- Product 1 & 2: Core feature pages
- Pricing: Plan tier descriptions and headers
- Launch: Major product announcement or changelog excerpt

Saves to gitignored data/corpus/marketing-corpus.json for copyright protection.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "corpus" / "marketing-corpus.json"

TARGETS_REGISTRY = [
    # 1. Frontier & Tech Flagships (7)
    {"name": "Apple", "domain": "apple.com", "category": "frontier"},
    {"name": "Google", "domain": "cloud.google.com", "category": "frontier"},
    {"name": "Anthropic", "domain": "anthropic.com", "category": "frontier"},
    {"name": "OpenAI", "domain": "openai.com", "category": "frontier"},
    {"name": "Tesla", "domain": "tesla.com", "category": "frontier"},
    {"name": "SpaceX", "domain": "spacex.com", "category": "frontier"},
    {"name": "Stripe", "domain": "stripe.com", "category": "frontier"},

    # 2. Developer & Infrastructure (7)
    {"name": "Vercel", "domain": "vercel.com", "category": "dev_infra"},
    {"name": "GitHub", "domain": "github.com", "category": "dev_infra"},
    {"name": "Supabase", "domain": "supabase.com", "category": "dev_infra"},
    {"name": "Cloudflare", "domain": "cloudflare.com", "category": "dev_infra"},
    {"name": "Datadog", "domain": "datadoghq.com", "category": "dev_infra"},
    {"name": "Snowflake", "domain": "snowflake.com", "category": "dev_infra"},
    {"name": "Twilio", "domain": "twilio.com", "category": "dev_infra"},

    # 3. Product & Design (6)
    {"name": "Linear", "domain": "linear.app", "category": "product_design"},
    {"name": "Figma", "domain": "figma.com", "category": "product_design"},
    {"name": "Notion", "domain": "notion.com", "category": "product_design"},
    {"name": "Retool", "domain": "retool.com", "category": "product_design"},
    {"name": "Webflow", "domain": "webflow.com", "category": "product_design"},
    {"name": "PostHog", "domain": "posthog.com", "category": "product_design"},

    # 4. Collaboration & Productivity (6)
    {"name": "Slack", "domain": "slack.com", "category": "collab_prod"},
    {"name": "Loom", "domain": "loom.com", "category": "collab_prod"},
    {"name": "Airtable", "domain": "airtable.com", "category": "collab_prod"},
    {"name": "Miro", "domain": "miro.com", "category": "collab_prod"},
    {"name": "Canva", "domain": "canva.com", "category": "collab_prod"},
    {"name": "Atlassian", "domain": "atlassian.com", "category": "collab_prod"},

    # 5. Fintech & Growth (5)
    {"name": "Ramp", "domain": "ramp.com", "category": "fintech_growth"},
    {"name": "Brex", "domain": "brex.com", "category": "fintech_growth"},
    {"name": "Shopify", "domain": "shopify.com", "category": "fintech_growth"},
    {"name": "Segment", "domain": "segment.com", "category": "fintech_growth"},
    {"name": "Intercom", "domain": "intercom.com", "category": "fintech_growth"},
]


def load_corpus(path=DEFAULT_CORPUS_PATH, create_if_missing=False):
    if not path.exists():
        if not create_if_missing:
            sys.exit(f"{path}: no corpus here; run init first")
        return {"version": "1.0", "updated_at": datetime.now(timezone.utc).isoformat(), "companies": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_corpus(data, path=DEFAULT_CORPUS_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def init_corpus(path=DEFAULT_CORPUS_PATH):
    corpus = load_corpus(path, create_if_missing=True)
    existing_names = {c["name"] for c in corpus["companies"]}
    added = 0
    for target in TARGETS_REGISTRY:
        if target["name"] not in existing_names:
            corpus["companies"].append({
                "name": target["name"],
                "domain": target["domain"],
                "category": target["category"],
                "surfaces": []
            })
            added += 1
    save_corpus(corpus, path)
    print(f"Initialized corpus at {path} ({len(corpus['companies'])} total companies, {added} added).")


def status_report(path=DEFAULT_CORPUS_PATH):
    corpus = load_corpus(path)
    companies = corpus.get("companies", [])
    print(f"\nCorpus Status: {path}")
    print(f"Total Companies: {len(companies)} / {len(TARGETS_REGISTRY)}")
    
    surfaces_total = 0
    headlines_total = 0
    categories = {}
    
    for c in companies:
        cat = c.get("category", "other")
        surfs = len(c.get("surfaces", []))
        surfaces_total += surfs
        h_count = sum(1 for s in c.get("surfaces", []) if (s.get("hero") or {}).get("headline"))
        headlines_total += h_count
        categories.setdefault(cat, []).append((c["name"], surfs, h_count))
        
    for cat, items in sorted(categories.items()):
        print(f"\nCategory: {cat} ({len(items)} companies)")
        for name, surfs, h_count in sorted(items):
            status = "✓ complete" if surfs >= 3 else f"partial ({surfs} surfaces)"
            print(f"  - {name.ljust(15)}: {status} ({h_count} headlines)")
            
    print(f"\nTotal Surfaces Captured: {surfaces_total}")
    print(f"Total Headlines: {headlines_total}")


def main():
    p = argparse.ArgumentParser(description="Marketing Corpus Harvester & Manager")
    sub = p.add_subparsers(dest="cmd", required=True)
    
    i_cmd = sub.add_parser("init", help="Initialize target companies registry in corpus JSON")
    i_cmd.add_argument("--path", type=Path, default=DEFAULT_CORPUS_PATH)
    
    s_cmd = sub.add_parser("status", help="Print harvest status across the 31 brands")
    s_cmd.add_argument("--path", type=Path, default=DEFAULT_CORPUS_PATH)
    
    args = p.parse_args()
    if args.cmd == "init":
        init_corpus(args.path)
    elif args.cmd == "status":
        status_report(args.path)


if __name__ == "__main__":
    main()
