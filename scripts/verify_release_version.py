"""Verify release tag and built distribution metadata use identical versions."""

import argparse
import re
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path


TAG_VERSION = re.compile(r"^v(?P<version>[0-9]+(?:\.[0-9]+){2}(?:[A-Za-z0-9.+-]*)?)$")


def distribution_version(artifact: Path) -> str:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as wheel:
            metadata_name = next(
                (name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")),
                None,
            )
            if metadata_name is None:
                raise ValueError(f"{artifact} has no wheel METADATA file")
            metadata = BytesParser().parsebytes(wheel.read(metadata_name))
            return metadata["Version"]

    match = re.search(r"-(?P<version>.+)\.tar\.gz$", artifact.name)
    if match is None:
        raise ValueError(f"Unsupported distribution artifact: {artifact}")
    return match.group("version")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="release tag, for example v2.0.0")
    parser.add_argument("artifacts", nargs="+", type=Path, help="wheel and/or source distribution")
    args = parser.parse_args(argv)

    tag_match = TAG_VERSION.fullmatch(args.tag)
    if tag_match is None:
        parser.error("tag must use vX.Y.Z format")
    expected_version = tag_match.group("version")

    for artifact in args.artifacts:
        actual_version = distribution_version(artifact)
        if actual_version != expected_version:
            raise SystemExit(
                f"Release tag {args.tag} does not match {artifact.name} version {actual_version}"
            )

    print(f"Release tag {args.tag} matches {len(args.artifacts)} distribution artifact(s)")


if __name__ == "__main__":
    main()
