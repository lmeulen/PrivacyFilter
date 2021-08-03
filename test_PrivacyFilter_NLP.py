import unittest
import re

from PrivacyFilter import PrivacyFilter


def file_to_samples(file, directory="test_samples", delimiter="~"):
    with open("{dir}/{file}".format(dir=directory, file=file)) as f:
        for line in f.readlines():
            line = line.rstrip()
            yield line.split(delimiter)


def run_test_function_with_data(self, function, sample, *args, **kwargs):
    dirty, clean = sample

    # Add spaces for easier regex
    dirty = " {} ".format(dirty)

    # Run cleaning function
    result = function(dirty, *args, **kwargs)
    result = self.pfilter.cleanup_text(result)

    # Replace any filtered output with <FILTERED> for easier runs
    result = re.sub("\<[A-Z_]+\>", "<FILTERED>", result)
    clean = re.sub("\<[A-Z_]+\>", "<FILTERED>", clean)

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


class PFTestNLP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pfilter = PrivacyFilter()
        cls.pfilter.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=False)


class TestNLP(PFTestNLP):
    def test_nlp(self):
        for sample in file_to_samples("nlp.txt"):
            run_test_function_with_data(self, self.pfilter.filter, sample, set_numbers_zero=False)


if __name__ == '__main__':
    unittest.main()
