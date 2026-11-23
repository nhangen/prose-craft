# Changelog

## Unreleased

- Skill: add a Marketing copy habit. Headlines run near six words and may stand as a single noun or open with a verb; strings of fragments and empty intensifiers are out.
- Skill: exempt headlines and taglines from the Complete sentences and Voice habits.
- Site: add a Marketing habit card.
- Site: rename the workbench to Prose Craft Live. The home page button now reads "Copy to Prose Craft Live".
- Site: the button copies your draft to the clipboard before it opens Prose Craft Live, where one keystroke (Cmd+V or Ctrl+V) pastes it. The old hash-fragment handoff never arrived, because the live page drops it. If the browser blocks the copy, the page stays put and says how to copy by hand.

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
