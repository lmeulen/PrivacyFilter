import importlib
import sys
import unittest
import warnings
from importlib.resources import files
from pathlib import Path


class TestPackageNamespace(unittest.TestCase):
    def test_test_modules_and_fixtures_live_under_test_directory(self):
        self.assertFalse(list(Path(".").glob("test_*.py")))
        self.assertTrue((Path("test") / "samples" / "nlp.txt").is_file())

    def test_supported_public_api_and_packaged_data(self):
        import privacyfilter

        self.assertEqual(privacyfilter.__version__, "2.0.0")
        self.assertTrue(callable(privacyfilter.PrivacyFilter))
        self.assertTrue(callable(privacyfilter.PIIFilter))
        self.assertTrue((files("privacyfilter.data") / "firstnames.csv").is_file())

    def test_legacy_privacyfilter_module_warns_and_reexports_public_api(self):
        sys.modules.pop("PrivacyFilter", None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            legacy = importlib.import_module("PrivacyFilter")

        self.assertIs(legacy.PrivacyFilter, importlib.import_module("privacyfilter").PrivacyFilter)
        self.assertEqual(len(caught), 1)
        self.assertIs(caught[0].category, DeprecationWarning)


if __name__ == "__main__":
    unittest.main()
