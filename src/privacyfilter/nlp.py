"""spaCy loading and entity interpretation adapter."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def load_model() -> Any:
    """Load PrivacyFilter's supported Dutch spaCy model lazily."""
    import spacy

    return spacy.load("nl_core_news_lg")


def filter_text(
    text: str,
    nlp: Callable[[str], Any],
    known_keywords: Mapping[str, str],
    numbers_to_zero: bool,
    capture_words: Sequence[str],
    blacklist_entities: Sequence[str],
    name_stopwords: set[str],
) -> str:
    """Interpret spaCy tokens while applying PrivacyFilter's replacement policy."""
    tagged_words = [
        (str(word), word.tag_, word.pos_, word.ent_type_) for word in nlp(text)
    ]
    filtered_words: list[tuple[str, str, str, str]] = []
    index = 0
    captured_words = ""
    captured_entity = ""

    for word, tags, word_type, entity_type in tagged_words:
        is_capture_word = word_type in capture_words
        if is_capture_word:
            captured_words += f"{word} "
            if (
                entity_type
                and entity_type not in blacklist_entities
                and (
                    word_type == "PROPN"
                    or word[:1].isupper()
                    or entity_type in {"DATE", "TIME"}
                )
            ):
                captured_entity = entity_type

        if (
            is_capture_word
            and index + 1 < len(tagged_words)
            and tagged_words[index + 1][2] in capture_words
        ):
            index += 1
            continue

        if is_capture_word:
            replacement = captured_words.strip()
            if captured_entity:
                replacement = f"<{captured_entity}>"
            elif captured_words[:1].isupper():
                replacement = known_keywords.get(replacement.casefold(), replacement)
        elif word_type == "NUM":
            replacement = "0" if numbers_to_zero else "<GETAL>"
        elif word[:1].isupper() and word not in name_stopwords:
            replacement = known_keywords.get(word.casefold(), word)
        else:
            replacement = word

        filtered_words.append((replacement, tags, word_type, captured_entity))
        index += 1
        captured_words = ""
        captured_entity = ""

    return "".join(
        (" " if word_type != "PUNCT" else "") + word
        for word, _, word_type, _ in filtered_words
    ).strip()
