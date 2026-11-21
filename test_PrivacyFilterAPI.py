import inspect
import unittest

from fastapi.testclient import TestClient

from PrivacyFilter import __version__
from PrivacyFilterAPI import privacyFilterApp


class TestPrivacyFilterAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(privacyFilterApp)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_filter_endpoint_is_synchronous_for_threadpool_execution(self):
        route = next(route for route in privacyFilterApp.routes if route.path == "/filter")

        self.assertFalse(inspect.iscoroutinefunction(route.endpoint))

    def test_root(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Welcome, please navigate to /filter", "version": __version__},
        )

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "version": __version__})

    def test_filter_without_nlp(self):
        response = self.client.post(
            "/filter",
            json={"text": "Jan woont op 12-12-2021.", "use_nlp": False},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Jan woont op <FILTERED>.")
        self.assertGreaterEqual(response.json()["time"], 0)

    def test_filter_with_nlp(self):
        response = self.client.post(
            "/filter",
            json={"text": "Jan woont op 12-12-2021.", "use_nlp": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "<FILTERED> woont op <FILTERED>.")

    def test_use_nlp_defaults_to_true(self):
        response = self.client.post("/filter", json={"text": "Jan woont hier."})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "<FILTERED> woont hier.")

    def test_openapi_version(self):
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["version"], __version__)

    def test_invalid_request(self):
        response = self.client.post("/filter", json={"text": 123})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
