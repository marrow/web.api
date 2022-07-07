# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture, importorskip, raises

from web.api.client import Interface
from web.api.processing import Body, Serialized, Text, Validated

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


@fixture
def iface_s():
	class SInterface(Serialized, Interface): pass
	
	interface = SInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()


class TestSerializedRetrieval:
	"""Serialized content retrieval attempts to decode returned content as appropriate."""
	
	def test_html(self, iface_s):
		importorskip('pyquery')
		
		result = iface_s.html.get()
		
		assert result('h1').length == 1
	
	def test_json(self, iface_s):
		result = iface_s.json.get()
		
		assert 'slideshow' in result
		assert not {'author', 'date', 'slides', 'title'} ^ set(result['slideshow'])
	
	def test_xml(self, iface_s):
		result = iface_s.xml.get()
		
		assert not {'title', 'date', 'author'} ^ set(result.keys())
