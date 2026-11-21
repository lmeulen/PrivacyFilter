import importlib.util
import unittest
from importlib.resources import files
from pathlib import Path


class TestPackageNamespace(unittest.TestCase):
    def test_test_modules_and_fixtures_live_under_test_directory(self):
        self.assertFalse(list(Path(".").glob("test_*.py")))
        self.assertTrue((Path("test") / "samples" / "nlp.txt").is_file())

    def test_supported_public_api_and_packaged_data(self):
        import privacyfilter

        self.assertEqual(privacyfilter.__version__, "2.0.1")
        self.assertTrue(callable(privacyfilter.PrivacyFilter))
        self.assertTrue(callable(privacyfilter.PIIFilter))
        self.assertTrue((files("privacyfilter.data") / "firstnames.csv").is_file())

    def test_openssl_is_only_certificate_extra(self):
        metadata = Path("pyproject.toml").read_text(encoding="utf-8")
        runtime_dependencies = metadata.split("[project.optional-dependencies]", maxsplit=1)[0]
        certificate_extra = metadata.split("[project.optional-dependencies]", maxsplit=1)[1].split(
            "updater =", maxsplit=1
        )[0]

        self.assertNotIn("pyopenssl", runtime_dependencies.lower())
        self.assertIn("pyopenssl", certificate_extra.lower())

    def test_legacy_flat_modules_are_not_importable(self):
        for module in (
            "DataUpdater",
            "FilterCSVColumn",
            "GenerateCertificate",
            "PIIFilter",
            "PrivacyFilter",
            "PrivacyFilterAPI",
            "Processor",
            "RunExamples",
        ):
            self.assertIsNone(importlib.util.find_spec(module))


if __name__ == "__main__":
    unittest.main()
