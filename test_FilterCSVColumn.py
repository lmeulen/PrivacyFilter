import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import call, patch

import pandas as pd

import FilterCSVColumn


class TestFilterCsvColumn(unittest.TestCase):
    def test_main_directory_uses_nested_paths_and_skips_generated_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            nested = root / "nested"
            nested.mkdir()
            (root / "top.csv").write_text("text\nfirst\n", encoding="ISO-8859-1")
            (nested / "child.csv").write_text("text\nsecond\n", encoding="ISO-8859-1")
            (nested / "child_filtered.csv").write_text("text\nold\n", encoding="ISO-8859-1")

            with (
                patch("FilterCSVColumn.PrivacyFilter") as privacy_filter,
                patch("FilterCSVColumn.parse_csv_file") as parse_csv_file,
            ):
                FilterCSVColumn.main_directory(str(root), [0])

            privacy_filter.return_value.initialize.assert_called_once()
            self.assertCountEqual(
                parse_csv_file.call_args_list,
                [
                    call(
                        str(root / "top.csv"),
                        str(root / "top_filtered.csv"),
                        [0],
                        privacy_filter.return_value,
                        separator=",",
                    ),
                    call(
                        str(nested / "child.csv"),
                        str(nested / "child_filtered.csv"),
                        [0],
                        privacy_filter.return_value,
                        separator=",",
                    ),
                ],
            )

    def test_parse_csv_file_accepts_separator_and_deprecated_alias(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            inputfile = Path(temporary_directory) / "input.csv"
            outputfile = Path(temporary_directory) / "output.csv"
            inputfile.write_text("text;other\nhello;value\n", encoding="ISO-8859-1")

            class PassThroughFilter:
                def filter(self, value):
                    return value

            FilterCSVColumn.parse_csv_file(
                str(inputfile), str(outputfile), [0], PassThroughFilter(), separator=";"
            )
            self.assertEqual(pd.read_csv(outputfile, sep=";").iloc[0, 0], "hello")

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                FilterCSVColumn.parse_csv_file(
                    str(inputfile), str(outputfile), [0], PassThroughFilter(), seperator=";"
                )
            self.assertEqual(len(caught), 1)
            self.assertIs(caught[0].category, DeprecationWarning)


if __name__ == "__main__":
    unittest.main()
