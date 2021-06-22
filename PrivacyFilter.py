import time
import re
from flashtext import KeywordProcessor


class PrivacyFilter:

    def __init__(self):
        self.keyword_processor_case_sensitive = KeywordProcessor(case_sensitive=True)
        self.keyword_processor_case_insensitive = KeywordProcessor(case_sensitive=False)
        self.initialised = False

    def file_to_list(self, filename, minimum_length=0, drop_first=1):
        with open(filename, encoding='latin') as f:
            lst = [line.rstrip() for line in f]
        lst = list(dict.fromkeys(lst))
        if minimum_length > 0:
            lst = list(filter(lambda item: len(item) > minimum_length, lst))
        return lst[drop_first:]

    def initialize(self):

        for naam in self.file_to_list('datasets\\streets_Nederland.csv', minimum_length=5):
            for c in ['.', ',', ' ', ':', ';', '?', '!']:
                self.keyword_processor_case_insensitive.add_keyword(naam + c, '<ADRES>' + c)

        for naam in self.file_to_list('datasets\\places.csv'):
            for c in ['.', ',', ' ', ':', ';', '?', '!']:
                self.keyword_processor_case_insensitive.add_keyword(naam + c, '<PLAATS>' + c)

        for naam in self.file_to_list('datasets\\firstnames.csv'):
            self.keyword_processor_case_sensitive.add_keyword(naam, '<NAAM>')

        for naam in self.file_to_list('datasets\\lastnames.csv'):
            self.keyword_processor_case_sensitive.add_keyword(naam, '<NAAM>')

        for naam in self.file_to_list('datasets\\aandoeningen.csv'):
            self.keyword_processor_case_insensitive.add_keyword(naam, '<AANDOENING>')

        for naam in self.file_to_list('datasets\\medicijnen.csv'):
            self.keyword_processor_case_insensitive.add_keyword(naam, '<MEDICIJN>')

        self.initialised = True

    def remove_numbers(self, text, set_zero=True):
        if set_zero:
            return re.sub('\d', '0', text).strip()
        else:
            return re.sub(r'\w*\d\w*', '<GETAL>', text).strip()

    def remove_dates(self, text):
        text = re.sub("\d{2}[- /.]\d{2}[- /.]\d{,4}", "<DATUM> ", text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
            "<DATUM> ",
            text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
            "<DATUM> ",
            text)
        return text

    def remove_email(self, text):
        return re.sub("(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
                      "<EMAIL>",
                      text)

    def remove_postal_codes(self, text):
        return re.sub("[0-9]{4}[ ]?[A-Z]{2}([ ,.:;])", "<POSTCODE>\\1", text)

    def filter(self, inputtext, set_numbers_zero=True):
        if not self.initialised:
            return inputtext

        text = " " + inputtext + " "

        text = self.remove_dates(text)
        text = self.remove_email(text)
        text = self.remove_postal_codes(text)
        text = self.remove_numbers(text, set_numbers_zero)

        text = self.keyword_processor_case_insensitive.replace_keywords(text)
        text = self.keyword_processor_case_sensitive.replace_keywords(text)

        return text.strip()


def insert_newlines(string, every=64):
    """
    Insert a new line every n characters.
    Parameters
    ----------
    string Text to adapt
    every After each <every> character, insert a newline

    Returns
    -------
    Adapted string
    """
    return '\n'.join(string[i:i + every] for i in range(0, len(string), every))


def main():
    zin = "De mogelijkheden zijn sinds 2014 groot geworden, zeker vergeleken met 2012, hè Kees? Het systeem maakt " \
          "verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24–01–2011 (of 24 jan 21 " \
          "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is " \
          "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier " \
          "ranitidine voor. "

    print(insert_newlines(zin, 120))
    start = time.time()

    pfilter = PrivacyFilter()
    pfilter.initialize()

    print('\nInitialisation time %4.0f msec' % ((time.time() - start) * 1000))

    start = time.time()
    nr_sentences = 1000
    for i in range(0, nr_sentences):
        zin = pfilter.filter(zin, set_numbers_zero=False)
    print('Deduce time per sentence %4.2f msec\n' % ((time.time() - start) * 1000 / nr_sentences))
    print(insert_newlines(zin, 120))


if __name__ == "__main__":
    main()