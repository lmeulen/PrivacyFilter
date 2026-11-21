"""Deprecated compatibility module; import :mod:`privacyfilter.api` instead."""

import warnings

warnings.warn(
    "PrivacyFilterAPI module is deprecated; use 'privacyfilter.api'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter.api import privacyFilterApp

__all__ = ["privacyFilterApp"]
