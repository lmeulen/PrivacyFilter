"""Deprecated compatibility module; import from :mod:`privacyfilter.processor` instead."""

import warnings

warnings.warn(
    "Processor module is deprecated; use 'privacyfilter.processor'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter.processor import KeywordProcessor, TrieNode

__all__ = ["KeywordProcessor", "TrieNode"]
