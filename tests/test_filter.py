import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent.parent / "skills" / "prose-craft" / "scripts"
FILTER = str(HERE / "prose-filter.py")
FIXER = ("import sys\nt = sys.stdin.read().split('DRAFT\\n', 1)[1]\n"
         "print(t.replace('\\u2014', ', ').replace('In parallel, I ran it.', 'I ran it in parallel.'))\n")
STUBBORN = "import sys\nprint(sys.stdin.read().split('DRAFT\\n', 1)[1])\n"
BROKEN = "import sys\nsys.exit(3)\n"


def run(args, text):
    return subprocess.run([sys.executable, FILTER] + args, input=text, capture_output=True, text=True)


class Check(unittest.TestCase):
    def test_sentence_starting_with_inline_code_is_not_an_opener(self):
        self.assertEqual(run(["check", "-"], "`prose-filter.py` with `check` and `run` modes is here.\n").returncode, 0)

    def test_inline_code_after_a_preposition_is_still_an_opener(self):
        self.assertEqual(run(["check", "-"], "In `main`, the loop runs.\n").returncode, 1)

    def test_clean_text_passes(self):
        self.assertEqual(run(["check", "-"], "The model scores well. Furthermore, it runs fast.\n").returncode, 0)

    def test_em_dash_is_reported_with_its_line(self):
        r = run(["check", "-"], "Fine line.\nThe run—which failed—restarted.\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("line 2: dash used as punctuation", r.stdout)

    def test_adverbial_opener_is_reported(self):
        r = run(["check", "-"], "In parallel, I ran it.\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("line 1: sentence opens with an adverbial", r.stdout)

    def test_a_subject_ending_in_ing_is_not_a_participial_opener(self):
        for text in ("Nothing runs on its own, because the plugin installs no hooks.\n",
                     "Something broke, and the build stopped.\n",
                     "Everything passed, so the release shipped.\n"):
            self.assertEqual(run(["check", "-"], text).returncode, 0, text)

    def test_a_noun_ending_in_ing_is_not_a_participial_opener(self):
        for text in ("Marketing copy ends on its best fact, such as a number.\n",
                     "Engineering teams ship, and the changelog records it.\n",
                     "Accounting rules differ, so the totals do too.\n"):
            self.assertEqual(run(["check", "-"], text).returncode, 0, text)

    def test_a_participial_opener_is_still_reported(self):
        r = run(["check", "-"], "Following the lecture, she wrote up her notes.\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("sentence opens with an adverbial", r.stdout)

    def test_fenced_and_inline_code_are_skipped(self):
        self.assertEqual(run(["check", "-"], "Use `a — b` here.\n\n```\nIn code — ignored\n```\n").returncode, 0)

    def test_a_hard_wrapped_sentence_is_not_split_at_the_line_break(self):
        self.assertEqual(run(["check", "-"], "The change adds a timeout\nin the delivery client and retries.\n").returncode, 0)

    def test_list_items_are_checked_individually(self):
        r = run(["check", "-"], "- Furthermore, this passes.\n- In parallel, this fails.\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("line 2", r.stdout)

    def test_heading_and_wrapped_paragraph_report_physical_lines(self):
        draft = "# Results\nIn June, we shipped. We kept\nthe schedule.\nAfter lunch, we rested."
        r = run(["check", "-"], draft)
        self.assertEqual(r.returncode, 1)
        self.assertEqual([line.split(":")[0] for line in r.stdout.splitlines()
                          if line.startswith("- line")], ["- line 2", "- line 4"])

    @unittest.skipUnless(shutil.which("node"), "node is required for the browser checker")
    def test_browser_reports_physical_lines_after_heading_and_wrap(self):
        draft = "# Results\nIn June, we shipped. We kept\nthe schedule.\nAfter lunch, we rested."
        script = "console.log(JSON.stringify(require('./site/prose-filter.js').check(process.argv[1])))"
        result = subprocess.check_output(["node", "-e", script, draft], cwd=Path(__file__).resolve().parents[1])
        self.assertEqual([row[:2] for row in json.loads(result)], [[2, "opener"], [4, "opener"]])

    def test_missing_file_is_a_usage_error(self):
        self.assertEqual(run(["check", "/nonexistent/x.txt"], "").returncode, 2)

    def test_invalid_utf8_is_a_read_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.txt"
            path.write_bytes(b"\xff")
            r = run(["check", str(path)], "")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


class Run(unittest.TestCase):
    def agent(self, source):
        d = tempfile.mkdtemp()
        p = Path(d) / "agent.py"
        p.write_text(source)
        return f"{sys.executable} {p}"

    def test_agent_fixes_the_draft_and_clean_text_comes_out(self):
        r = run(["run", "--agent", self.agent(FIXER), "-"], "In parallel, I ran it.\nThe run—restarted.\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("—", r.stdout)
        self.assertIn("I ran it in parallel.", r.stdout)

    def test_agent_that_never_fixes_is_rejected_after_max_rounds(self):
        calls = Path(tempfile.mkdtemp()) / "calls"
        source = ("import sys\nfrom pathlib import Path\n"
                  f"p = Path({str(calls)!r})\n"
                  "p.write_text(str(int(p.read_text()) + 1) if p.exists() else '1')\n"
                  "print(sys.stdin.read().split('DRAFT' + chr(10), 1)[1])\n")
        r = run(["run", "--agent", self.agent(source), "--max-rounds", "2", "-"], "The run—restarted.\n")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn("rejected after 2 rounds", r.stderr)
        self.assertEqual(calls.read_text(), "2")

    def test_revision_keeps_existing_signoffs_in_prose_and_code(self):
        draft = "We—shipped.\n\nSigned-off-by: Pat\n\n```text\n  Signed-off-by: Sam\n```\n"
        r = run(["run", "--agent", self.agent(FIXER), "-"], draft)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, draft.replace("—", ", "))

    def test_empty_normalized_revision_is_an_agent_error(self):
        trailer = "import sys\nprint('Signed-off-by: Placeholder <x@example.test>')\n"
        r = run(["run", "--agent", self.agent(trailer), "-"], "The run—restarted.\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("empty", r.stderr.lower())

    def test_invalid_utf8_from_agent_is_a_runtime_error(self):
        source = "import sys\nsys.stdout.buffer.write(b'\\xff')\n"
        r = run(["run", "--agent", self.agent(source), "-"], "The run—restarted.\n")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_agent_command_syntax_and_launch_errors_are_reported_as_runtime_errors(self):
        malformed = run(["run", "--agent", "'", "-"], "The run—restarted.\n")
        self.assertEqual(malformed.returncode, 2)
        self.assertNotIn("Traceback", malformed.stderr)
        missing = run(["run", "--agent", "/missing/prose-agent", "-"], "The run—restarted.\n")
        self.assertEqual(missing.returncode, 2)
        self.assertNotIn("Traceback", missing.stderr)

    def test_a_failing_agent_is_an_error_not_a_pass(self):
        r = run(["run", "--agent", self.agent(BROKEN), "-"], "The run—restarted.\n")
        self.assertEqual(r.returncode, 2)

    def test_clean_input_never_calls_the_agent(self):
        r = run(["run", "--agent", self.agent(BROKEN), "-"], "The run restarted.\n")
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
