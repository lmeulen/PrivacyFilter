"""Verify release tag and built distribution metadata use identical versions."""

import argparse
import re
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path


TAG_VERSION = re.compile(r"^v(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?)$")
VERSION_FILE = re.compile(r'^__version__\s*=\s*["\'](?P<version>[^"\']+)["\']\s*$', re.MULTILINE)


def source_version(version_file: Path) -> str:
    match = VERSION_FILE.search(version_file.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"Could not find __version__ assignment in {version_file}")
    return match.group("version")


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
    parser.add_argument("tag", help="release tag, for example v2.0.0 or v2.0.0rc1")
    parser.add_argument("artifacts", nargs="*", type=Path, help="wheel and/or source distribution")
    parser.add_argument("--version-file", type=Path, help="version source to validate before build")
    args = parser.parse_args(argv)

    tag_match = TAG_VERSION.fullmatch(args.tag)
    if tag_match is None:
        parser.error("tag must use vX.Y.Z or vX.Y.ZrcN/aN/bN format")
    if not args.artifacts and args.version_file is None:
        parser.error("provide distribution artifacts and/or --version-file")
    expected_version = tag_match.group("version")

    if args.version_file is not None:
        actual_version = source_version(args.version_file)
        if actual_version != expected_version:
            raise SystemExit(
                f"Release tag {args.tag} does not match {args.version_file} version {actual_version}"
            )

    for artifact in args.artifacts:
        actual_version = distribution_version(artifact)
        if actual_version != expected_version:
            raise SystemExit(
                f"Release tag {args.tag} does not match {artifact.name} version {actual_version}"
            )

    sources = len(args.artifacts) + (1 if args.version_file is not None else 0)
    print(f"Release tag {args.tag} matches {sources} version source(s)")


if __name__ == "__main__":
    main()
