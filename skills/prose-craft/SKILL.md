---
name: prose-craft
description: Use when drafting, rewriting, revising or editing prose a person will read (reports, papers, READMEs, PR bodies, emails, marketing copy, slide text, fiction) and sentence openers, length variety, structure and story shape matter. Applies a no-adverbial-opener rule, a no-em-dash rule and measured habits, to new text and to rewrites of existing text. For a pattern-by-pattern AI-tell scrub of finished text, humanizer or avoid-ai-writing; for rewriting it into real prose, this skill.
---

# Prose Craft

Part 1 holds hard rules that apply without exception, and a script enforces them. Part 2 lists habits measured on baseline model output. It was revised after a blind test that the first version lost, so treat it as a starting recipe, not a proven one.

## 1. Hard rules

1. **Subject first. No sentence opens with an adverbial.** That covers prepositional phrases ("In parallel", "On the test set", "With alpha fixed"), infinitive purpose phrases ("To choose alpha"), adverbial clauses ("Because", "When", "If", "As in"), participial openers ("Following the lectures,"), and `-ly` adverbs ("Quietly,"). Move the phrase after the verb: "I ran an ablation in parallel." "The model scores 76.02% on the test set."
   Conjunctive transitions are fine: Furthermore, Additionally, Moreover, However, Therefore, Thus, Also, Then, Still, Finally, Meanwhile, Similarly, Likewise, Nevertheless, Nonetheless. "Instead of ..." is an adverbial; bare "Instead," is a transition.
2. **No em dashes.** Never write "—" or a spaced " - " as punctuation. Use a period, a comma, a colon or parentheses. An en dash is fine inside a number range (July 22–October 26). Em dashes were the most common fault in blind tests, flagged in nine of thirteen pairs.
3. Check before you hand anything over. Save the draft to a file and run `python3 <skill dir>/scripts/prose-filter.py check FILE`, where `<skill dir>` is the folder that holds this SKILL.md (`${CLAUDE_PLUGIN_ROOT}/skills/prose-craft` in Claude Code). It exits 0 when clean and prints each violation with its line when not. Fix every hit and run it again. If you cannot run scripts, search the draft for "—", then list the first words of every sentence by eye.

This rule comes from the skill's author, not from the reference authors. Austen, Hopkins and Feynman all use such openers (0.08 to 0.22 of sentences), and the unprompted model baseline sits at 0.06 to 0.48. The rule wins over imitation.

## 2. Measured habits (Phase 0 baselines)

Write the shape you want. A prohibition alone leaves room to negotiate.

- **Sentence length:** vary it. Model fiction has 0.44 of its sentences at six words or fewer; the masters and technical writers sit at 0.08 to 0.19. Let a long sentence carry the reasoning and use a short one only where it earns the stress.
- **Completeness:** a PR body, explanation, how-to or email is a document someone will act on. Give it the full account: what changed or what to do, why, the caveats and the next step. Do not compress it to a summary line. Blind picks preferred the thorough version over the terse one every time.
- **Structure follows the register:** reference material (PR bodies, how-tos, guides) takes headings and lists where the reader will scan. A short chat message, an email or a story takes plain paragraphs.
- **Contrast:** state the claim directly. Skip "isn't X. It's Y" and "Not one. Not two." constructions.
- **Serial comma:** put a comma before the "and" or "or" that closes a list of three or more ("a period, a comma, or a colon"). This is the author's house style, not a measured habit, and the filter does not check it.
- **Specifics:** put the vivid fact first, not in a Challenge / Solution / Results template. Slide titles state the conclusion, not the topic.
- **Fiction and dialogue:** pick a name, place and opening line you have not used in this session. Unprompted stories converge (lighthouse keepers, "thirty-one years"). Build toward a turn or a climax. In dialogue, let characters talk around the thing, keep small concrete details, and hold tension. Terse, sterile exchanges and fragment strings read as machine-made.
- **Complete sentences:** every sentence has its own subject and finite verb. A clause that begins with Because, That or a bare noun phrase and stops there is a fragment, so attach it to the sentence it belongs to. Do not break one sentence in two ("I talked to a guy. At the reception.").
- **Run-ons:** one sentence holds one main idea. When two unrelated facts are joined by "and" or a comma, make two sentences.
- **Answer the prompt as written:** open an argument or explanation by naming its topic. Honor the stated audience, so "no background" means no jargon and no phrases like "in plain terms" that announce the register instead of using it.
- **Narrative:** show the character's state through what they do and say, in plain declarative sentences. Skip stage-direction lines that explain a gesture ("He did not go to the window") and screenplay-style cues. A nervous person fidgets or talks too fast; the narration does not say so.
- **Closings:** end on a concrete line that fits the document, then stop. Finish every paragraph you start. Skip a sign-off phrase nobody would say in that setting (a PR body or ticket does not end "Let me know if you have questions"), and never stop mid-sentence.
- **Voice:** write as an educated adult would: complete sentences, a warm and human register in emails, a clear close. Skip run-ons and padded word-count filler.
- **Facts:** use only the facts supplied. Do not add a date, number, person or meta-note to the deliverable.
- **Commit messages:** `area: imperative subject` under about 72 characters, then a body that states the problem, the change and the effect. No trailer you were not asked for.

## Not a goal

AI-detector scores. The blocklist detector scored all 121 baseline samples as human, so passing it proves nothing.

The filter checks only the two Part 1 rules. Part 2 is guidance and nothing verifies it.
