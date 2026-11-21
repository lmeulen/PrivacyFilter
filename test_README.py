import doctest
import re
import unittest
from pathlib import Path


class TestReadmeExamples(unittest.TestCase):
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
