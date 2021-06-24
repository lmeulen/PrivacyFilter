import re
from annotate import *


def filter(text):

    if not text:
        return text

    # Replace < and > symbols
    text = text.replace("<", "(")
    text = text.replace(">", ")")

    text = annotate_names(text)
    text = annotate_institution(text)
    text = annotate_residence(text)
    text = annotate_postalcode(text)
    text = annotate_phonenumber(text)
    text = annotate_date(text)
    text = annotate_email(text)
    text = annotate_url(text)

    return text


if __name__ == "__main__":
    orig = u"Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen (e: j.jnsen@email.com, " \
            u"t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht.Hij werd op 10 oktober door arts Peter de " \
            u"Visser ontslagen van de kliniek van het UMCU. "
    filtered = filter(orig)
    print(orig)
    print(filtered)
