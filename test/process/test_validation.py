# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture

from web.api.client import Interface
from web.api.processing import Validated


class TInterface(Validated, Interface): pass


@fixture
def iface():
	return TInterface('https://httpbin.org/')


class TestValidation:
	def test_success(self, iface):
		__import__('wdb').set_trace()
		result = iface.status[200].get()
	
	#def test_redirection(self, iface):
	#	result = iface.status[302].get()
	#	__import__('wdb').set_trace()
	
	def test_client_error(self, iface):
		__import__('wdb').set_trace()
		result = iface.status[400].get()
	
	def test_server_error(self, iface):
		__import__('wdb').set_trace()
		result = iface.status[500].get()

