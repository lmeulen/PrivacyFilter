import re
import unittest
import re

from PrivacyFilter import PrivacyFilter


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
    result = re.sub("\<[A-Z]+\>", "<FILTERED>", result)
    clean = re.sub("\<[A-Z]+\>", "<FILTERED>", clean)

    # Do the assertion
    self.assertEqual(
        result,
        clean,
        msg="\r\n\"{input}\" failed.\r\n"
            "Filtered output was: \"{output}\".\r\n"
            "Filtered output should have been: \"{correct}\"".format(
                input=dirty[1:-1],  # Remove pre/append spaces.
                correct=clean,
                output=result
            )
    )


class PFTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pfilter = PrivacyFilter()
        cls.pfilter.initialize(clean_accents=True, nlp_filter=False)


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
            run_test_function_with_data(self, self.pfilter.remove_numbers, sample, set_zero=False)

    def test_numbers_set_zero_true(self):
        for sample in file_to_samples("numbers_zeroes.txt"):
            run_test_function_with_data(self, self.pfilter.remove_numbers, sample, set_zero=True)


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
            run_test_function_with_data(self, self.pfilter.filter, sample, set_numbers_zero=False, nlp_filter=False)


if __name__ == '__main__':
    unittest.main()
