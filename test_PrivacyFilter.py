import unittest

from PrivacyFilter import PrivacyFilter


def file_to_samples(file, directory="test_samples", delimiter="~"):
    with open("{dir}/{file}".format(dir=directory, file=file)) as f:
        for line in f.readlines():
            line = line.rstrip()
            yield tuple(line.split(delimiter))


def run_test_function_with_data(self, function, sample, *args, **kwargs):
    dirty, clean = sample
    result = function(dirty, *args, **kwargs)
    self.assertEqual(
        result,
        clean,
        msg="\r\n\"{input}\" failed.\r\n"
            "Filtered output was: \"{output}\".\r\n"
            "Filtered output should have been: \"{correct}\"".format(
                input=dirty,
                correct=clean,
                output=result
            )
    )


class PFTest(unittest.TestCase):
    def setUp(self):
        pass
        self.pfilter = PrivacyFilter()
        self.pfilter.initialize(clean_accents=True, nlp_filter=False)


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

    def test_numbers(self):
        for sample in file_to_samples("numbers.txt"):
            run_test_function_with_data(self, self.pfilter.remove_numbers, sample)


if __name__ == '__main__':
    unittest.main()
