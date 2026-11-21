import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

import DataUpdater


class TestDataUpdater(unittest.TestCase):
    def test_filter_and_save_writes_canonical_package_data_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_directory = Path(temporary_directory) / "privacyfilter_data"
            dataframe = pd.DataFrame({"name": ["Beta", "Alpha", "Alpha"]})

            with patch.object(DataUpdater, "DATA_DIRECTORY", data_directory):
                DataUpdater.filter_and_save(
                    dataframe,
                    "name",
                    "names.csv",
                    min_length=0,
                    filter_verbs=False,
                )

            self.assertFalse((Path("datasets") / "names.csv").exists())
            self.assertEqual(
                (data_directory / "names.csv").read_text(encoding="utf-8"),
                "name\nAlpha\nBeta\n",
            )

    def test_get_response_uses_timeout_and_raises_for_http_errors(self):
        response = Mock()
        with patch.object(DataUpdater.HTTP_SESSION, "get", return_value=response) as get:
            self.assertIs(DataUpdater.get_response("https://example.test/data"), response)

        get.assert_called_once_with("https://example.test/data", timeout=DataUpdater.HTTP_TIMEOUT)
        response.raise_for_status.assert_called_once()

    def test_get_response_wraps_request_failures_with_url(self):
        with patch.object(
            DataUpdater.HTTP_SESSION,
            "get",
            side_effect=DataUpdater.requests.Timeout("slow source"),
        ):
            with self.assertRaisesRegex(RuntimeError, "https://example.test/data"):
                DataUpdater.get_response("https://example.test/data")

    def test_https_retry_adapter_retries_transient_get_failures(self):
        adapter = DataUpdater.HTTP_SESSION.adapters["https://"]

        self.assertEqual(adapter.max_retries.total, 3)
        self.assertIn(429, adapter.max_retries.status_forcelist)
        self.assertEqual(adapter.max_retries.backoff_factor, 0.5)

    def test_download_file_writes_only_successful_response_content(self):
        response = Mock(content=b"dataset")
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "raw" / "data.xml"
            with patch.object(DataUpdater, "get_response", return_value=response):
                DataUpdater.download_file("https://example.test/data", destination)

            self.assertEqual(destination.read_bytes(), b"dataset")

    def test_update_diseases_reports_changed_source_layout(self):
        with patch.object(DataUpdater, "get_soup") as get_soup:
            get_soup.return_value.find.return_value = None
            with self.assertRaisesRegex(ValueError, "disease list"):
                DataUpdater.update_diseases()

    def test_update_firstnames_rejects_empty_xml_dataset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            download_directory = Path(temporary_directory)
            (download_directory / "RAW_names").mkdir()
            with (
                patch.object(DataUpdater, "DOWNLOAD_DIRECTORY", download_directory),
                patch.object(
                    DataUpdater,
                    "download_file",
                    side_effect=lambda _url, destination: destination.write_text("<names/>", encoding="utf-8"),
                ),
            ):
                with self.assertRaisesRegex(ValueError, "no <voornaam> values"):
                    DataUpdater.update_firstnames()


if __name__ == "__main__":
    unittest.main()
