"""Deprecated compatibility module; use ``python -m privacyfilter.updater`` instead."""

import warnings

warnings.warn(
    "DataUpdater module is deprecated; use 'privacyfilter.updater'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter.updater import *  # noqa: F403


if __name__ == "__main__":
    update_datasets()  # noqa: F405
