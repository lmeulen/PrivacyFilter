"""Deprecated compatibility script; use :mod:`privacyfilter.examples` instead."""

import runpy
import warnings

warnings.warn(
    "RunExamples module is deprecated; use 'privacyfilter.examples'",
    DeprecationWarning,
    stacklevel=2,
)

if __name__ == "__main__":
    runpy.run_module("privacyfilter.examples", run_name="__main__")
