# Changelog

## 0.1.2

- Move `scripts/` into `skills/prose-craft/scripts/` so any skill install (Codex installer, OpenCode, a manual copy) brings the filter with it.
- Skill: call the filter by a path relative to the skill folder.
- README: add OpenCode discovery paths and invocation.

## 0.1.1

- Skill: add a serial comma habit (house style, not checked by the filter).
- Skill: say how to run the filter outside Claude Code, where `${CLAUDE_PLUGIN_ROOT}` does not exist.
- README: add install notes for OpenCode and Codex.

## 0.1.0

- Skill with two hard rules (subject first, no em dashes) and measured writing habits.
- Filter script with a check mode and a run-until-clean mode for any agent command.
- Dash-only checker script.
