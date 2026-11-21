"""Deprecated compatibility module; use ``python -m privacyfilter.csv_filter`` instead."""

import runpy
import warnings

warnings.warn(
    "FilterCSVColumn module is deprecated; use 'privacyfilter.csv_filter'",
    DeprecationWarning,
    stacklevel=2,
)

from privacyfilter.csv_filter import *  # noqa: F403


if __name__ == "__main__":
    runpy.run_module("privacyfilter.csv_filter", run_name="__main__")
