"""Deprecated compatibility module; import from :mod:`privacyfilter` instead."""

import warnings

warnings.warn(
    "PrivacyFilter module is deprecated; use 'from privacyfilter import PrivacyFilter'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter import PrivacyFilter, __version__, insert_newlines

__all__ = ["PrivacyFilter", "__version__", "insert_newlines"]
