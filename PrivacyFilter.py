import time
import re
import os
import unicodedata
#from flashtext import KeywordProcessor
import nl_core_news_sm
from Processor import KeywordProcessor


class PrivacyFilter:

    def __init__(self):
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.keyword_processor_names = KeywordProcessor(case_sensitive=True)
        self.url_re = None
        self.initialised = False
        self.clean_accents = True
        self.nr_keywords = 0
        self.nlp = None
        self.use_nlp = False

        ##### CONSTANTS #####
        self._punctuation = ['.', ',', ' ', ':', ';', '?', '!']

    def file_to_list(self, filename, drop_first=True):
        items_count = 0
        items = []

        with open(filename, "r", encoding="utf-8") as f:
            if drop_first:
                f.readline()

            for line in f.readlines():
                items_count += 1
                line = line.rstrip()
                line = self.remove_accents(line)  # TODO: move to dataupdater to
                items.append(line)

        self.nr_keywords += items_count
        return items

    def initialize(self, clean_accents=True, nlp_filter=True):

        # Add words with an append character to prevent replacing partial words by tags.
        # E.g. there is a street named AA and a verb AABB, with this additional character
        # would lead to <ADRES>BB which is incorrect. Another way to solve this might be the
        # implementation of a token based algorithm.

        fields = {
            os.path.join('datasets', 'firstnames.csv'): {"replacement": "<NAAM>", "punctuation": self._punctuation},
            os.path.join('datasets', 'lastnames.csv'): {"replacement": "<NAAM>", "punctuation": self._punctuation},
            os.path.join('datasets', 'places.csv'): {"replacement": "<PLAATS>", "punctuation": None},
            os.path.join('datasets', 'streets_Nederland.csv'): {"replacement": "<ADRES>", "punctuation": None},
            os.path.join('datasets', 'diseases.csv'): {"replacement": "<AANDOENING>", "punctuation": None},
            os.path.join('datasets', 'medicines.csv'): {"replacement": "<MEDICIJN>", "punctuation": None},
            os.path.join('datasets', 'nationalities.csv'): {"replacement": "<NATIONALITEIT>", "punctuation": None},
            os.path.join('datasets', 'countries.csv'): {"replacement": "<LAND>", "punctuation": None},
        }

        for field in fields:
            for name in self.file_to_list(field):
                self.keyword_processor.add_keyword(name, fields[field]["replacement"], fields[field]["punctuation"])

        for name in self.file_to_list(os.path.join('datasets', 'firstnames.csv')):
            self.keyword_processor_names.add_keyword(name, "<NAAM>")

        for name in self.file_to_list(os.path.join('datasets', 'lastnames.csv')):
            self.keyword_processor_names.add_keyword(name, "<NAAM>")

        # Make the URL regular expression
        # https://stackoverflow.com/questions/827557/how-do-you-validate-a-url-with-a-regular-expression-in-python
        ul = '\u00a1-\uffff'  # Unicode letters range (must not be a raw string).

        # IP patterns
        ipv4_re = r'(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)(?:\.(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)){3}'
        ipv6_re = r'\[?((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,'\
                  r'4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{'\
                  r'1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2['\
                  r'0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,'\
                  r'3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|['\
                  r'1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,'\
                  r'2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|((['\
                  r'0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2['\
                  r'0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:['\
                  r'0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2['\
                  r'0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,'\
                  r'5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\]?'

        # Host patterns
        hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
        # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
        domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
        tld_re = (
                r'\.'                                # dot
                r'(?!-)'                             # can't start with a dash
                r'(?:[a-z' + ul + '-]{2,63}'         # domain label
                r'|xn--[a-z0-9]{1,59})'              # or punycode label
                r'(?<!-)'                            # can't end with a dash
                r'\.?'                               # may have a trailing dot
        )
        host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'

        self.url_re = re.compile(
            r'((?:[a-z0-9.+-]*):?//)?'                                  # scheme is validated separately
            r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'                           # user:pass authentication
            r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'
            r'(?::\d{2,5})?'                                            # port
            r'(?:[/?#][^\s]*)?',                                        # resource path
            re.IGNORECASE
        )

        if nlp_filter:
            self.nlp = nl_core_news_sm.load()
            self.use_nlp = True

        self.clean_accents = clean_accents
        self.initialised = True

    @staticmethod
    def remove_numbers(text, set_zero=True):
        if set_zero:
            return re.sub('\d', '0', text).strip()
        else:
            return re.sub(r'\w*\d\w*', '<GETAL>', text).strip()

    @staticmethod
    def remove_times(text):
        return re.sub('(\d{1,2})[.:](\d{1,2})?([ ]?(am|pm|AM|PM))?', '<TIJD>', text)

    @staticmethod
    def remove_dates(text):
        text = re.sub("\d{2}[- /.]\d{2}[- /.]\d{,4}", "<DATUM>", text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
            "([- /.]{,2}(\d{4}|\d{2}))?)",
            "<DATUM>", text)

        text = re.sub(
            "(\d{1,2}[^\w]{,2}(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec))[- /.]((\d{4}|\d{2}))?",
            "<DATUM>", text)
        return text

    @staticmethod
    def remove_email(text):
        return re.sub("(([a-zA-Z0-9_+]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))"
                      "(?![^<]*>)",
                      "<EMAIL>",
                      text)

    def remove_url(self, text):
        text = re.sub(self.url_re, "<URL>", text)
        return text

    @staticmethod
    def remove_postal_codes(text):
        return re.sub(r"\b([0-9]{4}\s?[a-zA-Z]{2})", "<POSTCODE>", text)

    @staticmethod
    def remove_accents(text):
        text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore')
        return str(text.decode("utf-8"))

    @staticmethod
    def doc2string(doc):
        result = ""
        prev = ""
        for X in doc:
            if not X.ent_type_:
                result += X.text
            else:
                if prev == "<":
                    result += X.text
                else:
                    result += "<" + X.ent_type_ + ">"
            result += " "
            prev = X.text
        return result

    def filter_keyword_processors(self, text):
        text += ' '  # Add a space after the sentence to fix sentences which do not end with correct punctuation.
        text = self.keyword_processor.replace_keywords(text)
        text = self.keyword_processor_names.replace_keywords(text)
        return text[:-1]  # Remove the trailing space

    def filter_regular_expressions(self, text, set_numbers_zero=True):
        text = self.remove_url(text)
        text = self.remove_dates(text)
        text = self.remove_times(text)
        text = self.remove_email(text)
        text = self.remove_postal_codes(text)
        text = self.remove_numbers(text, set_numbers_zero)
        return text

    def filter_nlp(self, txt):
        if not self.nlp:
            self.initialize(clean_accents=self.clean_accents, nlp_filter=True)
        doc = self.nlp(txt)
        txt = self.doc2string(doc)
        return txt

    @staticmethod
    def cleanup_text(txt):
        result = txt
        result = re.sub("< ", "<", result)
        result = re.sub(" >", ">", result)
        result = re.sub("<<", "<", result)
        result = re.sub(">>", ">", result)
        result = re.sub("<GPE>", "<LOCATIE>", result)
        result = re.sub("<PERSON>", "<NAAM>", result)
        result = re.sub("<NAAM> <NAAM>", "<NAAM>", result)
        result = re.sub("<ADRES> <GETAL>", "<ADRES>", result)
        result = re.sub(" ([ ,.:;?!])", "\\1", result)
        result = result.strip()
        return result

    @staticmethod
    def full_cleanup_text(txt):
        result = txt
        result = re.sub("\<.*?\>", "<FILTERED>", result)
        result = re.sub(" ([ ,.:;?!])", "\\1", result)
        result = result.strip()
        return result

    def filter(self, inputtext, set_numbers_zero=False, nlp_filter=True):
        if not self.initialised:
            self.initialize()

        text = " " + inputtext + " "

        if self.clean_accents:
            text = self.remove_accents(text)

        text = self.filter_regular_expressions(text, set_numbers_zero)
        text = self.filter_keyword_processors(text)
        if nlp_filter:
            text = self.filter_nlp(text)

        return self.cleanup_text(text)


def insert_newlines(string, every=64, window=10):
    """
    Insert a new line every n characters. If possible, break
    the sentence at a space close to the cutoff point.
    Parameters
    ----------
    string Text to adapt
    every Maximum length of each line
    window The window to look for a space

    Returns
    -------
    Adapted string
    """
    result = ""
    from_string = string
    while len(from_string) > 0:
        cut_off = every
        if len(from_string) > every:
            while (from_string[cut_off - 1] != ' ') and (cut_off > (every - window)):
                cut_off -= 1
        else:
            cut_off = len(from_string)
        part = from_string[:cut_off]
        result += part + '\n'
        from_string = from_string[cut_off:]
    return result[:-1]


def main():
    zin = "De mogelijkheden zijn sinds 2014 groot geworden, zeker vergeleken met 2012, hè Kees? Het systeem maakt " \
          "verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24-01-2011 (of 24 jan 21 " \
          "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is " \
          "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier " \
          "heparine ( https://host.com/dfgr/dfdew ) voor. Simòne. Ik heet Lexan."

    print(insert_newlines(zin, 120))

    start = time.time()
    pfilter = PrivacyFilter()
    pfilter.initialize(clean_accents=True, nlp_filter=True)
    print('\nInitialisation time       : %4.0f msec' % ((time.time() - start) * 1000))
    print('Number of forbidden words : ' + str(pfilter.nr_keywords))

    start = time.time()
    nr_sentences = 100
    for i in range(0, nr_sentences):
        zin = pfilter.filter(zin, set_numbers_zero=False, nlp_filter=True)

    print('Time per sentence         : %4.2f msec' % ((time.time() - start) * 1000 / nr_sentences))
    print()
    print(insert_newlines(zin, 120))


if __name__ == "__main__":
    main()
