import subprocess
import sys
import tempfile
import unittest
import zipfile
from importlib.metadata import version
from pathlib import Path

import privacyfilter


class TestReleaseVersion(unittest.TestCase):
    def test_runtime_version_matches_installed_distribution_metadata(self):
        self.assertEqual(privacyfilter.__version__, version("privacyfilter"))

    def test_release_validator_accepts_matching_wheel_and_sdist(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifacts = Path(temporary_directory)
            wheel = artifacts / "privacyfilter-2.0.0-py3-none-any.whl"
            with zipfile.ZipFile(wheel, "w") as archive:
                archive.writestr("privacyfilter-2.0.0.dist-info/METADATA", "Version: 2.0.0\n")
            sdist = artifacts / "privacyfilter-2.0.0.tar.gz"
            sdist.write_bytes(b"")

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/verify_release_version.py",
                    "v2.0.0",
                    str(wheel),
                    str(sdist),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("matches 2 version source", result.stdout)

    def test_release_validator_accepts_matching_source_version_before_build(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            version_file = Path(temporary_directory) / "_version.py"
            version_file.write_text('__version__ = "2.0.0rc1"\n', encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/verify_release_version.py",
                    "v2.0.0rc1",
                    "--version-file",
                    str(version_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("matches 1 version source", result.stdout)

    def test_release_validator_rejects_mismatched_or_invalid_tag_before_build(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            version_file = Path(temporary_directory) / "_version.py"
            version_file.write_text('__version__ = "2.0.0"\n', encoding="utf-8")
            mismatch = subprocess.run(
                [
                    sys.executable,
                    "scripts/verify_release_version.py",
                    "v2.0.1",
                    "--version-file",
                    str(version_file),
                ],
                capture_output=True,
                text=True,
            )
            invalid = subprocess.run(
                [
                    sys.executable,
                    "scripts/verify_release_version.py",
                    "v2.0.0.post1",
                    "--version-file",
                    str(version_file),
                ],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(mismatch.returncode, 0)
        self.assertIn("does not match", mismatch.stderr)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("vX.Y.ZrcN/aN/bN", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
