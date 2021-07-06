import PrivacyFilter
from unittest import TestCase


class TestPrivacyFilter(TestCase):
    pfilter = None

    # def __init__(self, *args, **kwargs):
    #     super(TestPrivacyFilter, self).__init__(*args, **kwargs)
    #     self.pfilter = PrivacyFilter.PrivacyFilter()
    #     self.pfilter.initialize(clean_accents=True, nlp_filter=False)

    @classmethod
    def setUpClass(cls):
        cls.pfilter = PrivacyFilter.PrivacyFilter()
        cls.pfilter.initialize(clean_accents=True, nlp_filter=False)

    def test_remove_numbers(self):
        self.assertEqual("Het getal is <GETAL>.",
                         self.pfilter.remove_numbers("Het getal is 10.", set_zero=False))
        self.assertEqual("Het getal is 00.",
                         self.pfilter.remove_numbers("Het getal is 10.", set_zero=True))
        self.assertEqual("Het getal is <GETAL>",
                         self.pfilter.remove_numbers("Het getal is 10", set_zero=False))
        self.assertEqual("Het getal is <GETAL>,<GETAL>",
                         self.pfilter.remove_numbers("Het getal is 10,32423523454", set_zero=False))
        self.assertEqual("Het getal is <GETAL>",
                         self.pfilter.remove_numbers("Het getal is 10", set_zero=False))
        self.assertEqual("<GETAL>",
                         self.pfilter.remove_numbers("10", set_zero=False))
        self.assertEqual("<GETAL> punten",
                         self.pfilter.remove_numbers("10 punten", set_zero=False))

    def test_remove_times(self):
        self.assertEqual("De tijd is <TIJD>.",
                         self.pfilter.remove_times("De tijd is 12:20."))
        self.assertEqual("De tijd is <TIJD>.",
                         self.pfilter.remove_times("De tijd is 1:20."))
        self.assertEqual("De tijd is <TIJD>",
                         self.pfilter.remove_times("De tijd is 1:20PM"))
        self.assertEqual("De tijd is <TIJD>",
                         self.pfilter.remove_times("De tijd is 1:20 am"))

    def test_remove_dates(self):
        self.assertEqual("De datum is <DATUM>.",
                         self.pfilter.remove_dates("De datum is 12 januari 2020."))
        self.assertEqual("De datum is <DATUM>",
                         self.pfilter.remove_dates("De datum is 12 januari 2020"))
        self.assertEqual("<DATUM>",
                         self.pfilter.remove_dates("12 jan 2020"))
        self.assertEqual("<DATUM>",
                         self.pfilter.remove_dates("12 jan 20"))
        self.assertEqual("<DATUM>",
                         self.pfilter.remove_dates("12-12-2020"))
        self.assertEqual("<DATUM>",
                         self.pfilter.remove_dates("12-12-20"))

    def test_remove_email(self):
        self.assertEqual("Mijn email is <EMAIL>",
                         self.pfilter.remove_email("Mijn email is naam@partij.nl"))
        self.assertEqual("Mijn email is <EMAIL>.",
                         self.pfilter.remove_email("Mijn email is naam@partij.nl."))
        self.assertEqual("<EMAIL>",
                         self.pfilter.remove_email("naam.naam@partij.nl"))
        self.assertEqual("<EMAIL>.",
                         self.pfilter.remove_email("naam@partij.nl.com."))

    def test_remove_url(self):
        self.assertEqual("Mijn website is <URL>",
                         self.pfilter.remove_url("Mijn website is http://www.website.land"))
        self.assertEqual("Mijn website is <URL>",
                         self.pfilter.remove_url("Mijn website is https://www.website.land"))
        self.assertEqual("Mijn website is <URL>",
                         self.pfilter.remove_url("Mijn website is ftp://www.website.land"))
        self.assertEqual("Mijn website is <URL>",
                         self.pfilter.remove_url("Mijn website is ftps://www.website.land"))
        self.assertEqual("Mijn website is <URL>",
                         self.pfilter.remove_url("Mijn website is https://www.website.land/domein/q?param=waarde"))

    def test_remove_postal_codes(self):
        self.assertEqual("Mijn postcode is <POSTCODE>",
                         self.pfilter.remove_postal_codes("Mijn postcode is 0000AA"))
        self.assertEqual("Mijn postcode is <POSTCODE>.",
                         self.pfilter.remove_postal_codes("Mijn postcode is 0000AA."))
        self.assertEqual("Mijn postcode is <POSTCODE>",
                         self.pfilter.remove_postal_codes("Mijn postcode is 0000 AA"))
        self.assertEqual("Mijn postcode is <POSTCODE>.",
                         self.pfilter.remove_postal_codes("Mijn postcode is 0000 AA."))
        self.assertEqual("Mijn postcode is 0<POSTCODE>",
                         self.pfilter.remove_postal_codes("Mijn postcode is 00000AA"))

    def test_remove_accents(self):
        self.assertEqual("Helene",
                         self.pfilter.remove_accents("Helène"))

    def test_filter_keyword_processors(self):
        self.assertEqual("Ik woon aan de <ADRES>, in <PLAATS>.",
                         self.pfilter.filter_keyword_processors(
                             "Ik woon aan de Maasstraat, in Rotterdam."))
        self.assertEqual("1 Mijn naam is <NAAM>.",
                         self.pfilter.filter_keyword_processors("1 Mijn naam is Kees."))
        self.assertEqual("2 Mijn naam is <NAAM>",
                         self.pfilter.filter_keyword_processors("2 Mijn naam is Jantine "))
        self.assertEqual("3 Mijn naam is <NAAM>",
                         self.pfilter.filter_keyword_processors("3 Mijn naam is Thomas"))
        self.assertEqual("4 Mijn naam is <NAAM>.",
                         self.pfilter.filter_keyword_processors("4 Mijn naam is thomas."))
        self.assertEqual("5 Mijn naam is <NAAM>",
                         self.pfilter.filter_keyword_processors("5 Mijn naam is Thomas "))
        self.assertEqual("6 Mijn naam is Thoms <NAAM>",
                         self.pfilter.filter_keyword_processors("6 Mijn naam is Thoms Janssen"))
        self.assertEqual("7 Mijn naam is <NAAM>",
                         self.pfilter.filter_keyword_processors("7 Mijn naam is Janssen"))
        self.assertEqual("8 Mijn naam is <NAAM> <NAAM>",
                         self.pfilter.filter_keyword_processors("8 Mijn naam is Thomas Janssen"))

    def test_filter_regular_expressions(self):
        self.assertEqual("De PC is <POSTCODE>, url <URL> en mail <EMAIL>.",
                         self.pfilter.filter_regular_expressions(
                             "De PC is 0000AA, url https://www.nu.nl en mail naam@host.fr.rr."))

    def test_cleanup_text(self):
        self.assertEqual("Mijn naam is <NAAM>",
                         self.pfilter.cleanup_text(" Mijn naam is <NAAM> "))

    def test_filter(self):
        zin = "De mogelijkheden zijn sinds 2014 groot geworden, zeker vergeleken met 2012, hè Kees? Het systeem " \
              "maakt verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is 24-01-2011 (" \
              "of 24 januari 2011). Ik ben te bereiken op naam@hostingpartner.nl en woon in Arnhem. Mijn adres is " \
              "Maasstraat 231, 1234AB. Mijn naam is Thomas Janssen en ik heb zweetvoeten. Oh ja, ik gebruik hier " \
              "heparine ( https://host.com/dfgr/dfdew ) voor. Simòne. Ik heet Lexan. Ik heet Piet  woon in Asten."
        res = "De mogelijkheden zijn sinds <GETAL> groot geworden, zeker vergeleken met <GETAL>, he <NAAM>? Het " \
              "systeem maakt verschillende bewerkingen mogelijk die hiervoor niet mogelijk waren. De datum is <DATUM> "\
              "(of <DATUM>). Ik ben te bereiken op <EMAIL> en woon in <PLAATS>. Mijn adres is <ADRES>, <POSTCODE>. "\
              "Mijn naam is <NAAM> en ik heb <AANDOENING>. Oh ja, ik gebruik hier <MEDICIJN> ( <URL> ) voor. "\
              "<NAAM>. Ik heet Lexan. Ik heet <NAAM> woon in <PLAATS>."
        self.assertEqual(res, self.pfilter.filter(zin, nlp_filter=False))
