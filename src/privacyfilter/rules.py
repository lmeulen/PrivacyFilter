"""Stateless regular-expression and output-formatting rules."""

import re
import unicodedata
from typing import Pattern


def build_url_pattern() -> Pattern[str]:
    """Build URL matcher retained from original PrivacyFilter URL policy."""
    unicode_letters = "\u00a1-\uffff"
    ipv4 = r"(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)(?:\.(?:0|25[0-5]|2[0-4]\d|1\d?\d?|[1-9]\d?)){3}"
    hostname = rf"[a-z{unicode_letters}0-9](?:[a-z{unicode_letters}0-9-]{{0,61}}[a-z{unicode_letters}0-9])?"
    domain = rf"(?:\.(?!-)[a-z{unicode_letters}0-9-]{{1,63}}(?<!-))*"
    tld = rf"\.(?!-)(?:[a-z{unicode_letters}-]{{2,63}}|xn--[a-z0-9]{{1,59}})(?<!-)\.?"
    host = rf"({hostname}{domain}{tld}|localhost)"
    return re.compile(
        rf"([a-z0-9.+-]*:?//)?(?:[^\s:@/]+(?::[^\s:@/]*)?@)?(?:{ipv4}|{host})(?::\d{{2,5}})?(?:[/?#][^\s]*)?",
        re.IGNORECASE,
    )


def remove_numbers(text: str, numbers_to_zero: bool) -> str:
    return (
        re.sub(r"\d", "0", text).strip()
        if numbers_to_zero
        else re.sub(r"\w*\d\w*", "<GETAL>", text).strip()
    )


def remove_times(text: str) -> str:
    return re.sub(r"(\d{1,2})[.:](\d{1,2})?([ ]?(am|pm|AM|PM))?", "<TIJD>", text)


def remove_dates(text: str) -> str:
    text = re.sub(r"\d{2}[- /.]\d{2}[- /.]\d{,4}", "<DATUM>", text)
    text = re.sub(
        r"(\d{1,2}[^\w]{,2}(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)([- /.]{,2}(\d{4}|\d{2}))?)",
        "<DATUM>",
        text,
    )
    return re.sub(
        r"(\d{1,2}[^\w]{,2}(jan|feb|mrt|apr|mei|jun|jul|aug|sep|okt|nov|dec))[- /.](\d{4}|\d{2})?",
        "<DATUM>",
        text,
    )


def remove_email(text: str) -> str:
    return re.sub(
        r"(([a-zA-Z0-9_+]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
        "<EMAIL>",
        text,
    )


def remove_postal_codes(text: str) -> str:
    return re.sub(r"\b([0-9]{4}\s?[a-zA-Z]{2})\b", "<POSTCODE>", text)


def remove_accents(text: str) -> str:
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")


def cleanup_text(result: str) -> str:
    result = re.sub(r"<[A-Z _]+>", "<FILTERED>", result)
    result = re.sub(r" ([ ,.:;?!])", r"\1", result)
    result = re.sub(r" +", " ", result)
    result = re.sub(r"\n +", "\n", result)
    return re.sub(r"( <FILTERED>)+", " <FILTERED>", result).strip()
