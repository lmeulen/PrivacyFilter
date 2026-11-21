"""Deprecated compatibility module; import from :mod:`privacyfilter` instead."""

import warnings

warnings.warn(
    "PIIFilter module is deprecated; use 'from privacyfilter import PIIFilter'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter import PIIFilter

__all__ = ["PIIFilter"]
