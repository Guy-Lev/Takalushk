from ..controllers.response_builder import APP_JSON

class TestBasicHealth(object):
    def test_single_healthcheck(self):
        assert APP_JSON