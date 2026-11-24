# Changelog

## 0.1.3

- Skill: add Marketing copy habit based on empirical study of 31 leading tech brands; headlines target ~6 words and at most 45 characters to preserve clean two-line hero wraps without stranded connectives; permits single noun fragments or active verbs while rejecting fragment triplets and empty intensifiers (#21 closing #20, #26 closing #25).
- Skill: exempt headlines and taglines from the Complete sentences and Voice habits.
- Filter: preserve author sign-offs and signatures during multi-round regeneration (#18, closing #12).
- Filter: report opener violations with their physical Markdown line numbers rather than normalized block-relative offsets (#19, closing #13).
- Site: add a Marketing habit card and typographic styles (`text-wrap: balance; hyphens: none` for headings; `text-wrap: pretty` for body copy) to eliminate awkward wrapping and split words (#25, #26).
- Site: expand the single Marketing habit card into three grouped categories (Marketing, Content, Structure) with click-to-flip example pairs on the back of every habit card.
- Site: rename the workbench to Prose Craft Live. The home page button now reads "Copy to Prose Craft Live", copying drafts to the clipboard for reliable 1-keystroke pasting (#9, #11).
- Tooling: add `scripts/harvest-marketing.py` and `scripts/marketing-stylo.py` to benchmark and lint marketing headlines against empirical thresholds.

## 0.1.2

- Move `scripts/` into `skills/prose-craft/scripts/` so any skill install (Codex installer, OpenCode, a manual copy) brings the filter with it.
- Skill: call the filter by a path relative to the skill folder.
- README: add OpenCode discovery paths and invocation.
- Filter: stop flagging nouns that end in -ing (Nothing, Something, Marketing, Engineering and similar) as participial openers.
- README: drop the notes that said the plugin was only tested in Claude Code.

## 0.1.1

- Skill: add a serial comma habit (house style, not checked by the filter).
- Skill: say how to run the filter outside Claude Code, where `${CLAUDE_PLUGIN_ROOT}` does not exist.
- README: add install notes for OpenCode and Codex.

## 0.1.0

- Skill with two hard rules (subject first, no em dashes) and measured writing habits.
- Filter script with a check mode and a run-until-clean mode for any agent command.
- Dash-only checker script.
