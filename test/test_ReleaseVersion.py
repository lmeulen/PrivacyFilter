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

        self.assertIn("matches 2 distribution artifact", result.stdout)

    def test_release_validator_rejects_mismatched_tag(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify_release_version.py", "2.0.0", "dist/privacyfilter-2.0.0.tar.gz"],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tag must use vX.Y.Z format", result.stderr)


if __name__ == "__main__":
    unittest.main()
