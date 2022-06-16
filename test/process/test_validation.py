# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture, raises

from web.api.client import Interface
from web.api.processing import Validated

try:
	from httpx import HTTPStatusError as HTTPError
except ImportError:
	from requests import HTTPError


class TInterface(Validated, Interface): pass


@fixture
def iface():
	interface = TInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()


class TestValidation:
	def test_success(self, iface):
		iface.status[200].get()
	
	#def test_redirection(self, iface):
	#	result = iface.status[302].get()
	#	__import__('wdb').set_trace()
	
	def test_client_error(self, iface):
		with raises(HTTPError):
			iface.status[400].get()
	
	def test_server_error(self, iface):
		with raises(HTTPError):
			iface.status[500].get()

