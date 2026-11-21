import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from privacyfilter import examples


class TestExamples(unittest.TestCase):
    def test_compare_escapes_untrusted_text_and_keeps_generated_highlight(self):
        origin, result = examples.compare(
            '<script>alert("x")</script> <b>source</b>',
            '<img src=x onerror=alert(1)>',
            "red",
        )

        self.assertIn('<b style="color:red;">', origin)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", origin)
        self.assertIn("&lt;b&gt;source&lt;/b&gt;", origin)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", result)
        self.assertNotIn("<script>", origin)
        self.assertNotIn("<img ", result)

    def test_main_escapes_filename_and_filter_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            examples_directory = temporary_path / "examples"
            examples_directory.mkdir()
            filename = "untrusted & filename.txt"
            (examples_directory / filename).write_text('<script>alert(1)</script>\n', encoding="utf-8")
            output_file = temporary_path / "results.html"

            with (
                patch.object(examples, "folder", str(examples_directory)),
                patch.object(examples, "output_file", str(output_file)),
                patch.object(examples, "PrivacyFilter") as privacy_filter,
            ):
                privacy_filter.return_value.filter.return_value = '<script>alert(2)</script>'
                privacy_filter.return_value.to_string.return_value = '<script>alert(3)</script>'
                examples.main()

            output = output_file.read_text(encoding="utf-8")
            self.assertIn("untrusted &amp; filename.txt", output)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", output)
            self.assertIn("&lt;script&gt;alert(2)&lt;/script&gt;", output)
            self.assertIn("&lt;script&gt;alert(3)&lt;/script&gt;", output)
            self.assertNotIn("<script>", output)
            self.assertNotIn("<img ", output)


if __name__ == "__main__":
    unittest.main()
