import pytest

def pytest_addoption(parser):
    parser.addoption("--url", action="store", help="Base URL for smoke-test")

@pytest.fixture
def url(request):
    return request.config.getoption("--url")
