import tempfile
import unittest
from pathlib import Path

from privacyfilter import PrivacyFilter
from privacyfilter.configuration import load_configuration, read_dataset
from privacyfilter.nlp import filter_text
from privacyfilter.rules import cleanup_text, remove_accents


class TestConfiguration(unittest.TestCase):
    def test_read_dataset_and_yaml_loader(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            dataset = directory / "names.csv"
            dataset.write_text("name\nAda\n", encoding="utf-8")
            config = directory / "filter.yaml"
            config.write_text(
                "\n".join(
                    [
                        "clean_accents: true",
                        "nlp_filter: false",
                        "wordlist_filter: true",
                        "regular_expressions: true",
                        "numbers_to_zero: false",
                        f"data_directory: {directory}",
                        "firstnames: names.csv",
                        "lastnames: names.csv",
                        "places: names.csv",
                        "streets: names.csv",
                        "diseases: names.csv",
                        "medicines: names.csv",
                        "nationalities: names.csv",
                        "countries: names.csv",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(read_dataset(dataset), ["Ada"])
            loaded = load_configuration(config, ["."])

        self.assertTrue(loaded.wordlist_filter)
        self.assertEqual(loaded.fields[str(dataset)]["replacement"], "<LAND>")


class TestRules(unittest.TestCase):
    def test_rules_keep_public_filter_behavior(self):
        self.assertEqual(remove_accents("Simòne"), "Simone")
        self.assertEqual(cleanup_text(" <NAAM>  , <LAND> "), "<FILTERED> , <FILTERED>")


class TestNlpAdapter(unittest.TestCase):
    def test_nlp_adapter_replaces_known_proper_name(self):
        class Token:
            tag_ = ""
            ent_type_ = ""

            def __init__(self, text, pos):
                self.text = text
                self.pos_ = pos

            def __str__(self):
                return self.text

        result = filter_text(
            "Ada 42",
            lambda _: [Token("Ada", "PROPN"), Token("42", "NUM")],
            {"ada": "<NAAM>"},
            False,
            ["PROPN", "NOUN"],
            ["WORK_OF_ART"],
            {"Er"},
        )
        self.assertEqual(result, "<NAAM> <GETAL>")


class TestPublicNaming(unittest.TestCase):
    def test_configuration_description_uses_correct_class_name(self):
        self.assertTrue(PrivacyFilter().to_string().startswith("PrivacyFilter("))


if __name__ == "__main__":
    unittest.main()
