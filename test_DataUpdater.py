import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import DataUpdater


class TestDataUpdater(unittest.TestCase):
    def test_filter_and_save_writes_canonical_package_data_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_directory = Path(temporary_directory) / "privacyfilter_data"
            dataframe = pd.DataFrame({"name": ["Beta", "Alpha", "Alpha"]})

            with patch.object(DataUpdater, "DATA_DIRECTORY", data_directory):
                DataUpdater.filter_and_save(
                    dataframe,
                    "name",
                    "names.csv",
                    min_length=0,
                    filter_verbs=False,
                )

            self.assertFalse((Path("datasets") / "names.csv").exists())
            self.assertEqual(
                (data_directory / "names.csv").read_text(encoding="utf-8"),
                "name\nAlpha\nBeta\n",
            )


if __name__ == "__main__":
    unittest.main()
