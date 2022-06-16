import pytest

from web.api.client import Interface


@pytest.fixture()
def iface():
	interface = Interface('https://httpbin.org/')
	yield interface
	interface._ua.close()
