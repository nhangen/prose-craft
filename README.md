# prose-craft

A Claude Code plugin that makes AI writing less bad. It is not trying to imitate a famous author. It removes the faults readers notice first.

It has two parts:

- **A skill.** `skills/prose-craft/SKILL.md` loads when the agent drafts or revises prose a person will read. Part 1 holds two hard rules: subject first (no sentence opens with an adverbial phrase) and no em dashes. Part 2 holds habits measured on baseline model output: varied sentence length, complete sentences, thorough documents, concrete closings.
- **A filter.** `scripts/prose-filter.py` checks finished text against the two hard rules and feeds the violations back to any agent until the text is clean. It has no dependencies beyond Python 3.

The skill shapes the draft as it is written. The filter checks the result. Nothing runs automatically: there are no hooks.

## Install

```bash
claude plugin marketplace add nhangen/claude-plugins
claude plugin install prose-craft@nhangen-tools
```

The skill loads on its own when a task matches its description, or you can load it by name with `/prose-craft`.

## Other harnesses

The skill is a standard `SKILL.md` folder, so any harness that reads Agent Skills can load it. Clone this repo, copy `skills/prose-craft` into the harness's skills directory, then ask for `prose-craft` by name or let the description trigger it.

Codex has a built-in installer that needs no clone:

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo nhangen/prose-craft --path skills/prose-craft
```

For OpenCode, or Codex per repository, clone and copy:

```bash
git clone https://github.com/nhangen/prose-craft
cp -R prose-craft/skills/prose-craft ~/.config/opencode/skills/   # OpenCode
cp -R prose-craft/skills/prose-craft .agents/skills/              # Codex, per repository
```

The installer copies only the skill folder. The filter is plain Python 3, so it runs anywhere, but you need a clone for `scripts/prose-filter.py`. I have only tested the plugin in Claude Code.

## The filter

Check a file:

```bash
python3 scripts/prose-filter.py check draft.md
```

It exits 0 when the text is clean, 1 when it finds violations (it prints each one with its line and a correction message), and 2 on a read error. Fenced code and inline code are skipped.

Have it regenerate until clean. The command receives the correction message on stdin and prints the corrected text on stdout:

```bash
python3 scripts/prose-filter.py run --agent "claude -p" draft.md
python3 scripts/prose-filter.py run --agent "codex exec -" draft.md
python3 scripts/prose-filter.py run --agent "ollama run MODEL" draft.md
```

`--max-rounds N` sets the number of attempts (default 3). The command exits 1 if the text still fails after the last round and 2 if the agent command fails. I have only tested it live with `claude -p`.

`scripts/reject-emdash.py` is a smaller checker for dashes alone.

## What the filter checks

1. No em dash and no spaced hyphen used as punctuation. An en dash inside a number range is fine.
2. No sentence opens with an adverbial: a prepositional phrase, an infinitive purpose phrase, a Because, When or If clause, a participial phrase or an -ly adverb. Transitions such as Furthermore, However and Therefore are fine.

It does not check grammar, fragments, run-ons, structure or voice. Those live in the skill as guidance, and nothing verifies them.

## Evidence

An open-weights model fine-tuned against em dashes cut its dash rate from 80% to 9% on a held-out set of prompts. The skill alone lost two of three blind tests against unprompted model output, and a third ended in a tie. Treat Part 2 of the skill as a starting recipe.

## Development

```bash
python3 -m unittest discover -s tests
```

Versions follow semver. The version lives in `.claude-plugin/plugin.json`, and each release gets a `vX.Y.Z` tag. See `CHANGELOG.md`.

## License

MIT.
