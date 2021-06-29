import time
import re
import os
import unicodedata
from flashtext import KeywordProcessor


class PrivacyFilter:

    def __init__(self):
        self.keyword_processor_case_sensitive = KeywordProcessor(case_sensitive=True)
        self.keyword_processor_case_insensitive = KeywordProcessor(case_sensitive=False)
        self.url_re = None
        self.initialised = False
        self.nr_keywords = 0

    def file_to_list(self, filename, minimum_length=0, drop_first=1):
        with open(filename, encoding='latin') as f:
            lst = [line.rstrip() for line in f]
        lst = list(dict.fromkeys(lst))
        self.nr_keywords += len(lst)
        if minimum_length > 0:
            lst = list(filter(lambda item: len(item) > minimum_length, lst))
        return lst[drop_first:]

    def initialize(self):

        # Add words with an append character to prevent replacing partial words by tags.
        # E.g. there is a street named AA and a verb AABB, with this additional character
        # would lead to <ADRES>BB which is incorrect. Another way to solve this might be the
        # implementation of a token based algorithm.
        for name in self.file_to_list(os.path.join('datasets', 'streets_Nederland.csv'), minimum_length=5):
            for c in ['.', ',', ' ', ':', ';', '?', '!']:
                self.keyword_processor_case_insensitive.add_keyword(name + c, '<ADRES>' + c)

        for name in self.file_to_list(os.path.join('datasets', 'places.csv')):
            for c in ['.', ',', ' ', ':', ';', '?', '!']:
                self.keyword_processor_case_insensitive.add_keyword(name + c, '<PLAATS>' + c)

        for name in self.file_to_list(os.path.join('datasets', 'firstnames.csv')):
            self.keyword_processor_case_sensitive.add_keyword(name, '<NAAM>')

        for name in self.file_to_list(os.path.join('datasets', 'lastnames.csv')):
            self.keyword_processor_case_sensitive.add_keyword(name, '<NAAM>')

        for name in self.file_to_list(os.path.join('datasets', 'diseases.csv')):
            self.keyword_processor_case_insensitive.add_keyword(name, '<AANDOENING>')

        for name in self.file_to_list(os.path.join('datasets', 'medicines.csv')):
            self.keyword_processor_case_insensitive.add_keyword(name, '<MEDICIJN>')

        for name in self.file_to_list(os.path.join('datasets', 'nationalities.csv')):
            self.keyword_processor_case_insensitive.add_keyword(name, '<NATIONALITEIT>')

        for name in self.file_to_list(os.path.join('datasets', 'countries.csv')):
            self.keyword_processor_case_insensitive.add_keyword(name, '<LAND>')

        # Make the URL regular expression
        # https://stackoverflow.com/questions/827557/how-do-you-validate-a-url-with-a-regular-expression-in-python
        ul = '\u00a1-\uffff'  # unicode letters range (must not be a raw string)
        # IP patterns
        ipv4_re = r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'
        ipv6_re = r'\[[0-9a-f:\.]+\]'
        # Host patterns
        hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
        domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'  # domain names have max length of 63 characters
        tld_re = (
                r'\.'  # dot 
                r'(?!-)'  # can't start with a dash 
                r'(?:[a-z' + ul + '-]{2,63}'  # domain label 
                                  r'|xn--[a-z0-9]{1,59})'  # or punycode label 
                                  r'(?<!-)'  # can't end with a dash 
                                  r'\.?'  # may have a trailing dot
        )
        host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'
        self.url_re = re.compile(
            r'(?:http|ftp)s?://'  # http(s):// or ftp(s)://
            r'(?:\S+(?::\S*)?@)?'  # user:pass authentication 
            r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'  # localhost or ip
                                                               r'(?::\d{2,5})?'  # optional port
                                                               r'(?:[/?#][^\s]*)?'  # resource path
            , re.IGNORECASE)

        self.initialised = True

    def remove_numbers(self, text, set_zero=True):
        if set_zero:
            return re.sub('\d', '0', text).strip()
        else:
            return re.sub(r'\w*\d\w*', '<GETAL>', text).strip()

    def remove_dates(self, text):
        text = re.sub("\d{2}[- /.]\d{2}[- /.]\d{,4}", "<DATUM>", text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
            "<DATUM> ", text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec)([- /.]{,2}(\d{4}|\d{2})){,1})(?P<n>\D)(?![^<]*>)",
            "<DATUM> ", text)
        return text

    def remove_email(self, text):
        return re.sub("(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
                      "<EMAIL>",
                      text)

    def remove_url(self, text):
        return re.sub(self.url_re, "<URL>", text)

    def remove_postal_codes(self, text):
        return re.sub("[0-9]{4}[ ]?[A-Z]{2}([ ,.:;])", "<POSTCODE>\\1", text)

    def remove_accents(self, text):
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore')
        return str(text.decode("utf-8"))

    def filter(self, inputtext, set_numbers_zero=True, remove_accents=True):
        if not self.initialised:
            self.initialize()

        # Add space at the beginning of the text and a dot t the end to assure all
        # words are found, also if e.g. the sentence ends with a word and not a dot
        # Both are removed at the end of this fucntion
        text = " " + inputtext + "."
        if remove_accents:
            text = self.remove_accents(text)
        text = self.remove_url(text)
        text = self.remove_dates(text)
        text = self.remove_email(text)
        text = self.remove_postal_codes(text)
        text = self.remove_numbers(text, set_numbers_zero)

        text = self.keyword_processor_case_insensitive.replace_keywords(text)
        text = self.keyword_processor_case_sensitive.replace_keywords(text)
        return text[:-1].strip()


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
          "verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24-01-2011 (of 24 jan 21 " \
          "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is " \
          "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier " \
          "heparine (https://host.com/dfgr/dfdew ) voor. Simòne. Ik heet Lexan."

    print(insert_newlines(zin, 120))

    start = time.time()
    pfilter = PrivacyFilter()
    pfilter.initialize()
    print('\nInitialisation time       : %4.0f msec' % ((time.time() - start) * 1000))
    print('Number of forbidden words : ' + str(pfilter.nr_keywords))

    start = time.time()
    nr_sentences = 1000
    for i in range(0, nr_sentences):
        zin = pfilter.filter(zin, set_numbers_zero=False, remove_accents=True)

    print('Time per sentence         : %4.2f msec' % ((time.time() - start) * 1000 / nr_sentences))
    print()
    print(insert_newlines(zin, 120))


if __name__ == "__main__":
    main()
