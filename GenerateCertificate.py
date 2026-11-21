"""Deprecated compatibility module; import :mod:`privacyfilter.certificates` instead."""

import warnings

warnings.warn(
    "GenerateCertificate module is deprecated; use 'privacyfilter.certificates'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter.certificates import generate_certificate

__all__ = ["generate_certificate"]
