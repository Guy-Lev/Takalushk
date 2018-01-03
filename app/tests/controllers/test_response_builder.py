import pytest
from ...controllers import response_builder as test_class
from flask import Flask, current_app
import unittest

app = Flask(__name__)
json = {"key": "key", "value": "value"}


class TestResponseBuilder(unittest.TestCase):
    def test_validate_message_negative(self):
        with pytest.raises(TypeError):
            test_class.validate_message("ABC")

    def test_validate_message_positive(self):
        test_class.validate_message(json)

    def test_ok(self):
        with app.app_context():
            response = test_class.ok(json, "100")
            self.assertEquals(response.status_code , 100)

    def test_bad_request(self):
        with app.app_context():
            response = test_class.bad_request(json, "200")
            self.assertEquals(response.status_code, 200)

    def test_server_error(self):
        with app.app_context():
            response = test_class.server_error(json, "500")
            self.assertEquals(response.status_code, 500)