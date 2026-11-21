import doctest
import re
import unittest
from pathlib import Path


class TestReadmeExamples(unittest.TestCase):
    def test_csv_and_updater_workflows_are_documented(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        for text in (
            "python -m privacyfilter.csv_filter --input input.csv --output filtered.csv --column 0 2",
            "python -m privacyfilter.csv_filter --directory incoming-csv --column 1",
            "semicolon-delimited (`;`) ISO-8859-1",
            "comma-delimited (`,`) ISO-8859-1",
            "`*_filtered.csv`",
            "python -m pip install -e '.[updater]'",
            "python -m privacyfilter.updater",
            "significant time, network bandwidth, memory, and disk space",
            "retry later",
        ):
            self.assertIn(text, readme)

    def test_library_usage_example(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        match = re.search(r"```pycon\n(.*?)```", readme, flags=re.DOTALL)

        self.assertIsNotNone(match, "README must contain a pycon usage example")
        example = doctest.DocTestParser().get_doctest(
            match.group(1),
            globs={},
            name="README library usage",
            filename="README.md",
            lineno=0,
        )
        runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
        runner.run(example)
        self.assertEqual(runner.failures, 0)


if __name__ == "__main__":
    unittest.main()
