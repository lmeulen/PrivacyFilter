"""Typed configuration and dataset loading for :class:`PrivacyFilter`."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import TypeAlias

import yaml

FieldOptions: TypeAlias = Mapping[str, str | Sequence[str] | None]
FieldMap: TypeAlias = Mapping[str | PathLike[str], FieldOptions]


@dataclass(frozen=True)
class FilterConfiguration:
    clean_accents: bool
    nlp_filter: bool
    wordlist_filter: bool
    regular_expressions: bool
    numbers_to_zero: bool
    fields: dict[str, dict[str, str | Sequence[str] | None]]


def read_dataset(path: str | PathLike[str], *, drop_header: bool = True) -> list[str]:
    """Read one-column CSV dataset and return its non-header values."""
    with Path(path).open(encoding="utf-8") as dataset:
        lines = dataset.read().splitlines()
    return lines[1:] if drop_header else lines


def load_configuration(
    filename: str | PathLike[str], punctuation: Sequence[str]
) -> FilterConfiguration:
    """Load legacy YAML configuration into validated initialization values."""
    with Path(filename).open(encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file)
    if not isinstance(data, dict):
        raise ValueError("Filter configuration must contain a mapping")

    required = (
        "clean_accents",
        "nlp_filter",
        "wordlist_filter",
        "regular_expressions",
        "numbers_to_zero",
        "data_directory",
        "firstnames",
        "lastnames",
        "places",
        "streets",
        "diseases",
        "medicines",
        "nationalities",
        "countries",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Filter configuration is missing: {', '.join(missing)}")

    data_directory = Path(data["data_directory"])
    replacements = {
        "firstnames": "<NAAM>",
        "lastnames": "<NAAM>",
        "places": "<PLAATS>",
        "streets": "<ADRES>",
        "diseases": "<AANDOENING>",
        "medicines": "<MEDICIJN>",
        "nationalities": "<NATIONALITEIT>",
        "countries": "<LAND>",
    }
    fields = {
        str(data_directory / data[key]): {
            "replacement": replacement,
            "punctuation": None
            if data["nlp_filter"] or replacement != "<NAAM>"
            else punctuation,
        }
        for key, replacement in replacements.items()
    }
    return FilterConfiguration(
        clean_accents=bool(data["clean_accents"]),
        nlp_filter=bool(data["nlp_filter"]),
        wordlist_filter=bool(data["wordlist_filter"]),
        regular_expressions=bool(data["regular_expressions"]),
        numbers_to_zero=bool(data["numbers_to_zero"]),
        fields=fields,
    )
