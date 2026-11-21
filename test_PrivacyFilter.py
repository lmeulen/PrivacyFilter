import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PrivacyFilter import PrivacyFilter, __version__


def file_to_samples(file, directory="test_samples", delimiter="~"):
    with open("{dir}/{file}".format(dir=directory, file=file), encoding="utf-8") as f:
        for line in f.readlines():
            line = line.rstrip()
            yield line.split(delimiter)


def run_test_function_with_data(self, function, sample, *args, **kwargs):
    dirty, clean = sample

    # Remove accents and add spaces for easier regex
    dirty = self.pfilter.remove_accents(dirty)
    dirty = " {} ".format(dirty)

    # Run cleaning function
    result = function(dirty, *args, **kwargs)
    result = self.pfilter.cleanup_text(result)

    # Replace any filtered output with <FILTERED> for easier runs
    result = re.sub(r"<[A-Z]+>", "<FILTERED>", result)
    clean = re.sub(r"<[A-Z]+>", "<FILTERED>", clean)

    # Do the assertion
    self.assertEqual(
        result,
        clean,
        msg="\r\n\"{input}\" failed.\r\n"
            "Filtered output was              : \"{output}\".\r\n"
            "Filtered output should have been : \"{correct}\"".format(
                input=dirty[1:-1],  # Remove pre/append spaces.
                correct=clean,
                output=result
            )
    )


class TestReleaseMetadata(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "2.0.0")

    def test_default_data_is_packaged(self):
        pfilter = PrivacyFilter()
        pfilter.initialize(nlp_filter=False, wordlist_filter=True)

        self.assertEqual(pfilter.filter("Arnhem"), "<FILTERED>")


class TestInitialization(unittest.TestCase):
    def test_reinitialization_resets_loaded_keywords_and_count(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            first_data = Path(temporary_directory) / "first.csv"
            second_data = Path(temporary_directory) / "second.csv"
            first_data.write_text("name\nQxzvplm\n", encoding="utf-8")
            second_data.write_text("name\nRykjvnt\n", encoding="utf-8")

            pfilter = PrivacyFilter()
            pfilter.initialize(
                nlp_filter=False,
                wordlist_filter=True,
                regular_expressions=False,
                fields={str(first_data): {"replacement": "<NAME>", "punctuation": None}},
            )
            self.assertEqual(pfilter.nr_keywords, 1)
            self.assertEqual(pfilter.filter("Qxzvplm"), "<FILTERED>")

            pfilter.initialize(
                nlp_filter=False,
                wordlist_filter=True,
                regular_expressions=False,
                fields={str(second_data): {"replacement": "<NAME>", "punctuation": None}},
            )

            self.assertEqual(pfilter.nr_keywords, 1)
            self.assertEqual(pfilter.filter("Qxzvplm"), "Qxzvplm")
            self.assertEqual(pfilter.filter("Rykjvnt"), "<FILTERED>")

    def test_reinitialization_disables_nlp_and_clears_model(self):
        pfilter = PrivacyFilter()
        pfilter.nlp = object()
        pfilter.use_nlp = True

        pfilter.initialize(nlp_filter=False, wordlist_filter=False)

        self.assertFalse(pfilter.use_nlp)
        self.assertIsNone(pfilter.nlp)

    def test_custom_yaml_uses_only_configured_name_datasets(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "firstnames.csv").write_text("name\nQxzvplm\n", encoding="utf-8")
            (directory / "lastnames.csv").write_text("name\nRykjvnt\n", encoding="utf-8")
            for filename in (
                "places.csv",
                "streets.csv",
                "diseases.csv",
                "medicines.csv",
                "nationalities.csv",
                "countries.csv",
            ):
                (directory / filename).write_text("name\n", encoding="utf-8")
            config = directory / "filter.yaml"
            config.write_text(
                "\n".join(
                    (
                        "clean_accents: true",
                        "nlp_filter: false",
                        "wordlist_filter: true",
                        "regular_expressions: false",
                        "numbers_to_zero: false",
                        f"data_directory: {directory}",
                        "firstnames: firstnames.csv",
                        "lastnames: lastnames.csv",
                        "places: places.csv",
                        "streets: streets.csv",
                        "diseases: diseases.csv",
                        "medicines: medicines.csv",
                        "nationalities: nationalities.csv",
                        "countries: countries.csv",
                    )
                ),
                encoding="utf-8",
            )

            pfilter = PrivacyFilter()
            pfilter.initialize_from_file(config)

            self.assertEqual(pfilter.filter("Qxzvplm Rykjvnt Jan"), "<FILTERED> <FILTERED> Jan")
            self.assertNotIn("jan", pfilter.known_keywords)
            self.assertEqual(pfilter.nr_keywords, 2)

    def test_lazy_nlp_loading_preserves_existing_configuration(self):
        class Token:
            def __init__(self, text, pos):
                self.text = text
                self.tag_ = ""
                self.pos_ = pos
                self.ent_type_ = ""

            def __str__(self):
                return self.text

        with tempfile.TemporaryDirectory() as temporary_directory:
            data = Path(temporary_directory) / "keywords.csv"
            data.write_text("name\nQxzvplm\n", encoding="utf-8")
            pfilter = PrivacyFilter()
            pfilter.initialize(
                nlp_filter=False,
                wordlist_filter=True,
                regular_expressions=False,
                numbers_to_zero=True,
                fields={str(data): {"replacement": "<NAME>", "punctuation": None}},
            )

            with patch.object(
                pfilter,
                "_load_nlp",
                side_effect=lambda: setattr(
                    pfilter,
                    "nlp",
                    lambda text: [Token("Qxzvplm", "PROPN"), Token("42", "NUM")],
                ),
            ):
                self.assertEqual(pfilter.filter("Qxzvplm 42", nlp_filter=True), "<FILTERED> 0")

            self.assertFalse(pfilter.use_nlp)
            self.assertTrue(pfilter.use_wordlist)
            self.assertFalse(pfilter.use_re)
            self.assertTrue(pfilter.numbers_to_zero)
            self.assertEqual(pfilter.nr_keywords, 1)
            self.assertEqual(pfilter.filter("Qxzvplm 42"), "<FILTERED> 00")


class PFTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pfilter = PrivacyFilter()
        cls.pfilter.initialize(clean_accents=True, nlp_filter=False, wordlist_filter=True, regular_expressions=True)


class TestAccents(PFTest):
    def test_clean_accents(self):
        for sample in file_to_samples("accents.txt"):
            run_test_function_with_data(self, self.pfilter.remove_accents, sample)


class TestRegex(PFTest):
    def test_url(self):
        for sample in file_to_samples("url.txt"):
            run_test_function_with_data(self, self.pfilter.remove_url, sample)

    def test_email(self):
        for sample in file_to_samples("email.txt"):
            run_test_function_with_data(self, self.pfilter.remove_email, sample)

    def test_date(self):
        for sample in file_to_samples("date.txt"):
            run_test_function_with_data(self, self.pfilter.remove_dates, sample)

    def test_postal_codes(self):
        for sample in file_to_samples("postal_codes.txt"):
            run_test_function_with_data(self, self.pfilter.remove_postal_codes, sample)

    def test_time(self):
        for sample in file_to_samples("time.txt"):
            run_test_function_with_data(self, self.pfilter.remove_times, sample)

    def test_numbers(self):
        for sample in file_to_samples("numbers.txt"):
            run_test_function_with_data(self, self.pfilter.remove_numbers, sample, numbers_to_zero=False)

    def test_numbers_set_zero_true(self):
        for sample in file_to_samples("numbers_zeroes.txt"):
            run_test_function_with_data(self, self.pfilter.remove_numbers, sample, numbers_to_zero=True)


class TestKeywordProcessor(PFTest):
    def test_names(self):
        for sample in file_to_samples("names.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)

    def test_places(self):
        for sample in file_to_samples("places.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)

    def test_streets(self):
        for sample in file_to_samples("streets.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)

    def test_diseases(self):
        for sample in file_to_samples("diseases.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)

    def test_countries(self):
        for sample in file_to_samples("countries.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)

    def test_nationalities(self):
        for sample in file_to_samples("nationalities.txt"):
            run_test_function_with_data(self, self.pfilter.filter_keyword_processors, sample)


class TestFilter(PFTest):
    def test_filter(self):
        for sample in file_to_samples("filter.txt"):
            run_test_function_with_data(self, self.pfilter.filter, sample)


if __name__ == '__main__':
    unittest.main()
