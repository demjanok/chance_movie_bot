"""
Unit tests for structured JSON and text logging configuration.
"""

import io
import json
import logging
import os
import shutil
import tempfile
import unittest

from logging_config import JSONFormatter, setup_logging


class TestJSONFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = JSONFormatter(service_name="test_service")

    def test_basic_json_formatting(self):
        record = logging.LogRecord(
            name="test_module",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=42,
            msg="Hello, world!",
            args=(),
            exc_info=None,
        )
        output = self.formatter.format(record)
        data = json.loads(output)

        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["logger"], "test_module")
        self.assertEqual(data["message"], "Hello, world!")
        self.assertEqual(data["line"], 42)
        self.assertEqual(data["service"], "test_service")
        self.assertTrue(data["timestamp"].endswith("Z"))
        self.assertNotIn("exception", data)

    def test_unicode_and_emojis(self):
        record = logging.LogRecord(
            name="movies_handler",
            level=logging.INFO,
            pathname="movies.py",
            lineno=100,
            msg="Фільм знайдено: 🎬 Інтерстеллар",
            args=(),
            exc_info=None,
        )
        record.__dict__["genre"] = "Фантастика"
        record.__dict__["rating"] = 8.6

        output = self.formatter.format(record)
        data = json.loads(output)

        self.assertEqual(data["message"], "Фільм знайдено: 🎬 Інтерстеллар")
        self.assertEqual(data["genre"], "Фантастика")
        self.assertEqual(data["rating"], 8.6)

    def test_extra_context_fields(self):
        record = logging.LogRecord(
            name="auth_service",
            level=logging.INFO,
            pathname="auth.py",
            lineno=20,
            msg="User login successful",
            args=(),
            exc_info=None,
        )
        record.__dict__["user_id"] = 12345
        record.__dict__["username"] = "john_doe"
        record.__dict__["ip"] = "192.168.1.1"

        output = self.formatter.format(record)
        data = json.loads(output)

        self.assertEqual(data["user_id"], 12345)
        self.assertEqual(data["username"], "john_doe")
        self.assertEqual(data["ip"], "192.168.1.1")
        # Ensure internal attributes are excluded
        self.assertNotIn("pathname", data)
        self.assertNotIn("relativeCreated", data)

    def test_exception_serialization(self):
        try:
            raise ValueError("Invalid movie ID provided")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="tmdb_service",
            level=logging.ERROR,
            pathname="tmdb.py",
            lineno=55,
            msg="Failed to fetch details",
            args=(),
            exc_info=exc_info,
        )
        output = self.formatter.format(record)
        data = json.loads(output)

        self.assertEqual(data["level"], "ERROR")
        self.assertIn("exception", data)
        self.assertEqual(data["exception"]["type"], "ValueError")
        self.assertEqual(data["exception"]["message"], "Invalid movie ID provided")
        self.assertIsInstance(data["exception"]["traceback"], list)
        self.assertTrue(len(data["exception"]["traceback"]) > 0)


class TestSetupLogging(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Reset and properly close logging handlers
        root = logging.getLogger()
        for handler in root.handlers:
            handler.close()
        root.handlers.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging_json_stdout(self):
        setup_logging(log_level="DEBUG", log_format="json")
        root = logging.getLogger()
        self.assertEqual(root.level, logging.DEBUG)
        self.assertTrue(len(root.handlers) >= 1)
        self.assertIsInstance(root.handlers[0].formatter, JSONFormatter)

    def test_setup_logging_text_stdout(self):
        setup_logging(log_level="INFO", log_format="text")
        root = logging.getLogger()
        self.assertEqual(root.level, logging.INFO)
        self.assertNotIsInstance(root.handlers[0].formatter, JSONFormatter)

    def test_setup_logging_with_file(self):
        log_file = os.path.join(self.temp_dir, "logs", "test_bot.log")
        setup_logging(log_level="INFO", log_format="json", log_file=log_file)

        logger = logging.getLogger("test_file_logger")
        logger.info("Writing to file test", extra={"test_key": "test_val"})

        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            data = json.loads(content)
            self.assertEqual(data["message"], "Writing to file test")
            self.assertEqual(data["test_key"], "test_val")

    def test_third_party_loggers_quieted(self):
        setup_logging(log_level="INFO", log_format="json", third_party_level="WARNING")
        for noisy in ["httpx", "httpcore", "telegram"]:
            self.assertEqual(logging.getLogger(noisy).level, logging.WARNING)


if __name__ == "__main__":
    unittest.main()
