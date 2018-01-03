import requests


class TestSmoke(object):
    def test_single_healthcheck(self, url):
        response = requests.get("{url}/healthcheck".format(url=url), verify=False)
        assert response.status_code == 200