import pytest

from web.api.client import Interface


@pytest.fixture()
def iface():
	return Interface('https://httpbin.org/')

