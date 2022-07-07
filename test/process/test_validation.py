# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture, raises

from web.api.client import Interface
from web.api.processing import Body, Text, Validated

try:
	from httpx import HTTPStatusError as HTTPError
except ImportError:
	from requests import HTTPError


@fixture
def iface_v():
	class VInterface(Validated, Interface): pass
	
	interface = VInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()


class TestValidation:
	def test_success(self, iface_v):
		iface_v.status[200].get()
	
	def test_client_error(self, iface_v):
		with raises(HTTPError):
			iface_v.status[400].get()
	
	def test_server_error(self, iface_v):
		with raises(HTTPError):
			iface_v.status[500].get()


@fixture
def iface_b():
	class BInterface(Body, Interface): pass
	
	interface = BInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()

@fixture
def iface_t():
	class TInterface(Text, Interface): pass
	
	interface = TInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()


class TestBodyRetrieval:
	"""Body retrieval returns response.content, which is binary."""
	
	def test_xml_binary(self, iface_b):
		result = iface_b.xml.get()
		assert result.startswith(b'<?xml')
	
	def test_xml_text(self, iface_t):
		result = iface_t.xml.get()
		assert result.startswith('<?xml')
