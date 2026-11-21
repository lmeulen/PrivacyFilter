import unittest
from pathlib import Path


class TestContributingGuide(unittest.TestCase):
    def test_current_workflow_and_tooling_are_documented(self):
        guide = Path("CONTRIBUTING.md").read_text(encoding="utf-8")

        for text in (
            "`master` is default and release branch",
            "pull request targeting `master`",
            "uv sync --extra dev --extra updater --locked",
            "uv run pytest -q",
            "uv run ruff check .",
            "uv run pip-audit --progress-spinner off",
            "uv lock --check",
            "warnings as errors",
            "vX.Y.ZrcN",
        ):
            self.assertIn(text, guide)

        self.assertNotIn("~~", guide)
        self.assertNotIn("succesfull", guide)


if __name__ == "__main__":
    unittest.main()
