from PrivacyFilter import PrivacyFilter


class PIIFilter(PrivacyFilter):

    def __init__(self):
        super().__init__()
        self.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=True, regular_expressions=True)

    def filter(self, text, clean_accents=True, nlp_filter=True, regexp_filter=True, wordlist_filter=True):
        # Assure that a string is parsed
        text = str(text)

        if clean_accents:
            text = self.remove_accents(text)

        if nlp_filter:
            text = self.filter_nlp(text)

        if regexp_filter:
            text = self.filter_regular_expressions(text)

        if wordlist_filter:
            text = self.filter_static(text)

        return self.cleanup_text(text)


if __name__ == "__main__":
    zin = "De mogelijkheden zijn sinds 2014 groot geworden, zeker vergeleken met 2012, hè Kees? Het systeem maakt " \
          "verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24-01-2011 (of 24 jan 21 " \
          "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is " \
          "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier " \
          "heparine ( https://host.com/dfgr/dfdew ) voor. Simòne. Ik heet Lexan."
    print(zin)
    pfilter = PIIFilter()
    zin2 = pfilter.filter(zin, clean_accents=True, nlp_filter=True, regexp_filter=True, wordlist_filter=True)
    print()
    print(zin2)
