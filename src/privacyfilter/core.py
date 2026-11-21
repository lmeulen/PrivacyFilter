import os
import re
import time
from importlib.resources import files
from os import PathLike

from . import nlp, rules
from .configuration import FieldMap, load_configuration, read_dataset
from .processor import KeywordProcessor

DEFAULT_DATA_DIRECTORY = files("privacyfilter.data")


class PrivacyFilter:
    def __init__(self):
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.keyword_processor_names = KeywordProcessor(case_sensitive=True)
        self.url_re = None
        self.initialised = False
        self.clean_accents = True
        self.nr_keywords = 0
        self.known_keywords = {}
        self.nlp = None
        self.use_nlp = False
        self.use_wordlist = False
        self.use_re = False
        self.numbers_to_zero = False
        ##### CONSTANTS #####
        self._punctuation = [".", ",", " ", ":", ";", "?", "!"]
        self._capture_words = ["PROPN", "NOUN"]
        self._nlp_blacklist_entities = ["WORK_OF_ART"]
        self._nlp_name_stopwords = {"Er"}

    def to_string(self) -> str:
        """Return current configuration in readable form."""
        return (
            f"PrivacyFilter(clean_accents={self.clean_accents}, use_nlp={self.use_nlp}, "
            f"use_wordlist={self.use_wordlist})"
        )

    def file_to_list(
        self, filename: str | PathLike[str], drop_first: bool = True
    ) -> list[str]:
        """Load dataset and update configured keyword count."""
        items = read_dataset(filename, drop_header=drop_first)
        self.nr_keywords += len(items)
        return items

    def initialize_from_file(self, filename: str | PathLike[str]) -> None:
        """Initialize filter from YAML configuration file."""
        configuration = load_configuration(filename, self._punctuation)
        self.initialize(
            clean_accents=configuration.clean_accents,
            nlp_filter=configuration.nlp_filter,
            wordlist_filter=configuration.wordlist_filter,
            regular_expressions=configuration.regular_expressions,
            numbers_to_zero=configuration.numbers_to_zero,
            fields=configuration.fields,
        )

    def initialize(
        self,
        clean_accents: bool = True,
        nlp_filter: bool = True,
        wordlist_filter: bool = False,
        regular_expressions: bool = True,
        numbers_to_zero: bool = False,
        fields: FieldMap | None = None,
    ) -> None:
        self.keyword_processor = KeywordProcessor(case_sensitive=False)
        self.keyword_processor_names = KeywordProcessor(case_sensitive=True)
        self.url_re = None
        self.initialised = False
        self.nr_keywords = 0
        self.known_keywords = {}
        self.nlp = None
        self.use_nlp = nlp_filter

        # Add words with an append character to prevent replacing partial words by tags.
        # E.g. there is a street named AA and a verb AABB, with this additional character
        # would lead to <ADRES>BB which is incorrect. Another way to solve this might be the
        # implementation of a token based algorithm.
        if fields is None:
            fields = {
                os.path.join(DEFAULT_DATA_DIRECTORY, "firstnames.csv"): {
                    "replacement": "<NAAM>",
                    "punctuation": None if nlp_filter else self._punctuation,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "lastnames.csv"): {
                    "replacement": "<NAAM>",
                    "punctuation": None if nlp_filter else self._punctuation,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "places.csv"): {
                    "replacement": "<PLAATS>",
                    "punctuation": None,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "streets_Nederland.csv"): {
                    "replacement": "<ADRES>",
                    "punctuation": None,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "diseases.csv"): {
                    "replacement": "<AANDOENING>",
                    "punctuation": None,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "medicines.csv"): {
                    "replacement": "<MEDICIJN>",
                    "punctuation": None,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "nationalities.csv"): {
                    "replacement": "<NATIONALITEIT>",
                    "punctuation": None,
                },
                os.path.join(DEFAULT_DATA_DIRECTORY, "countries.csv"): {
                    "replacement": "<LAND>",
                    "punctuation": None,
                },
            }

        names = []
        for field in fields:
            # If there is a punctuation list, use it.
            if fields[field]["punctuation"] is not None:
                for name in self.file_to_list(field):
                    if fields[field]["replacement"] == "<NAAM>":
                        names.append(name)
                    self.known_keywords[name.casefold()] = fields[field]["replacement"]
                    for c in self._punctuation:
                        self.keyword_processor.add_keyword(
                            "{n}{c}".format(n=name, c=c),
                            "{n}{c}".format(n=fields[field]["replacement"], c=c),
                        )
            else:
                for name in self.file_to_list(field):
                    if fields[field]["replacement"] == "<NAAM>":
                        names.append(name)
                    self.known_keywords[name.casefold()] = fields[field]["replacement"]
                    self.keyword_processor.add_keyword(
                        name, fields[field]["replacement"]
                    )

        if not nlp_filter:
            for name in names:
                self.keyword_processor_names.add_keyword(name, "<NAAM>")

        # Make the URL regular expression
        # https://stackoverflow.com/questions/827557/how-do-you-validate-a-url-with-a-regular-expression-in-python
        ul = "\u00a1-\uffff"  # Unicode letters range (must not be a raw string).

        # IP patterns
        ipv4_re = r"(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)(?:\.(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)){3}"
        ipv6_re = (
            r"\[?((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,"
            r"4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{"
            r"1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2["
            r"0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,"
            r"3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|["
            r"1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,"
            r"2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|((["
            r"0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2["
            r"0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:["
            r"0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2["
            r"0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,"
            r"5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\]?"
        )

        # Host patterns
        hostname_re = (
            r"[a-z" + ul + r"0-9](?:[a-z" + ul + r"0-9-]{0,61}[a-z" + ul + r"0-9])?"
        )
        # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
        domain_re = r"(?:\.(?!-)[a-z" + ul + r"0-9-]{1,63}(?<!-))*"
        tld_re = (
            r"\."  # dot
            r"(?!-)"  # can't start with a dash
            r"(?:[a-z" + ul + "-]{2,63}"  # domain label
            r"|xn--[a-z0-9]{1,59})"  # or punycode label
            r"(?<!-)"  # can't end with a dash
            r"\.?"  # may have a trailing dot
        )
        host_re = "(" + hostname_re + domain_re + tld_re + "|localhost)"

        self.url_re = re.compile(
            r"([a-z0-9.+-]*:?//)?"  # scheme is validated separately
            r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
            r"(?:" + ipv4_re + "|" + ipv6_re + "|" + host_re + ")"
            r"(?::\d{2,5})?"  # port
            r"(?:[/?#][^\s]*)?",  # resource path
            re.IGNORECASE,
        )

        if nlp_filter:
            self._load_nlp()
        self.use_wordlist = wordlist_filter
        self.clean_accents = clean_accents
        self.use_re = regular_expressions
        self.numbers_to_zero = numbers_to_zero

        self.initialised = True

    def _load_nlp(self) -> None:
        """Load spaCy only when NLP filtering is configured or requested."""
        self.nlp = nlp.load_model()

    remove_numbers = staticmethod(rules.remove_numbers)
    remove_times = staticmethod(rules.remove_times)
    remove_dates = staticmethod(rules.remove_dates)
    remove_email = staticmethod(rules.remove_email)

    def remove_url(self, text):
        text = re.sub(self.url_re, "<URL>", text)
        return text

    remove_postal_codes = staticmethod(rules.remove_postal_codes)
    remove_accents = staticmethod(rules.remove_accents)

    def filter_keyword_processors(self, text):
        text = self.keyword_processor.replace_keywords(text)
        text = self.keyword_processor_names.replace_keywords(text)
        return text

    def filter_regular_expressions(self, text):
        text = self.remove_url(text)
        text = self.remove_dates(text)
        text = self.remove_times(text)
        text = self.remove_email(text)
        text = self.remove_postal_codes(text)
        text = self.remove_numbers(text, self.numbers_to_zero)
        return text

    def filter_nlp(self, text: str) -> str:
        """Filter text through loaded spaCy adapter."""
        if self.nlp is None:
            self._load_nlp()
        return nlp.filter_text(
            text,
            self.nlp,
            self.known_keywords,
            self.numbers_to_zero,
            self._capture_words,
            self._nlp_blacklist_entities,
            self._nlp_name_stopwords,
        )

    cleanup_text = staticmethod(rules.cleanup_text)

    def filter(self, text: object, nlp_filter: bool | None = None) -> str:
        if not self.initialised:
            self.initialize()
        text = str(text)
        if self.clean_accents:
            text = self.remove_accents(text)

        use_nlp = self.use_nlp if nlp_filter is None else nlp_filter
        if use_nlp:
            text = self.filter_nlp(text)
        if self.use_re:
            text = self.filter_regular_expressions(text)

        if self.use_wordlist:
            text = self.filter_static(text)

        return self.cleanup_text(text)

    def filter_static(self, text: str) -> str:
        text = " " + text + " "
        text = self.filter_regular_expressions(text)
        text = self.filter_keyword_processors(text)
        return text


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
            while (from_string[cut_off - 1] != " ") and (cut_off > (every - window)):
                cut_off -= 1
        else:
            cut_off = len(from_string)
        part = from_string[:cut_off]
        result += part + "\n"
        from_string = from_string[cut_off:]
    return result[:-1]


def main():
    zin = (
        "De mogelijkheden zijn sinds 2014 groot geworden, zeker vergeleken met 2012, hè Kees? Het systeem maakt "
        "verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24-01-2011 (of 24 jan 21 "
        "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is "
        "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier "
        "heparine ( https://host.com/dfgr/dfdew ) voor. Simòne. Ik heet Lexan."
    )

    print(insert_newlines(zin, 120))

    start = time.time()
    pfilter = PrivacyFilter()
    pfilter.initialize_from_file("filter.yaml")
    print("\nInitialisation time       : %4.0f msec" % ((time.time() - start) * 1000))
    print("Number of forbidden words : " + str(pfilter.nr_keywords))

    start = time.time()
    nr_sentences = 100
    for _ in range(nr_sentences):
        zin2 = pfilter.filter(zin)

    print(
        "Time per sentence         : %4.2f msec"
        % ((time.time() - start) * 1000 / nr_sentences)
    )
    print()
    print(insert_newlines(zin2, 120))


if __name__ == "__main__":
    main()
