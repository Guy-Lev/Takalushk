import requests


HOST = "localhost"
PORT = "9000"
ACCEPT_TEST_BASE_URL = "http://{host}:{port}".format(host=HOST, port=PORT)

class TestBasicHealth(object):
    def test_single_healthcheck(self):
        assert requests.get("{base_url}/healthcheck".format(base_url=ACCEPT_TEST_BASE_URL)).status_code == 200
