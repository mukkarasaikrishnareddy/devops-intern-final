#!/usr/bin/env python3
"""
test_hello.py - Unit tests for the DevOps HTTP application (hello.py).
"""

import threading
import time
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
import hello

TEST_PORT = 18080

class TestDevOpsHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start hello.py HTTP server in a daemon thread on port 18080."""
        cls.server = HTTPServer(("127.0.0.1", TEST_PORT), hello.DevOpsHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        # Give server time to bind and listen
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        """Shutdown the test HTTP server."""
        cls.server.shutdown()
        cls.server.server_close()

    def test_root_endpoint(self):
        """GET / should return 200 OK and 'Hello, DevOps!'"""
        url = f"http://127.0.0.1:{TEST_PORT}/"
        with urllib.request.urlopen(url, timeout=2) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertEqual(body, "Hello, DevOps!")

    def test_health_endpoint(self):
        """GET /health should return 200 OK and 'healthy'"""
        url = f"http://127.0.0.1:{TEST_PORT}/health"
        with urllib.request.urlopen(url, timeout=2) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertEqual(body, "healthy")

    def test_not_found(self):
        """GET /invalid should return 404 Not Found"""
        url = f"http://127.0.0.1:{TEST_PORT}/invalid"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url, timeout=2)
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

if __name__ == "__main__":
    unittest.main()
