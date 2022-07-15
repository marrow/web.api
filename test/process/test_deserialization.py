# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture, importorskip

from web.api.client import Interface
from web.api.processing import Serialized


class TInterface(Serialized, Interface): pass


@fixture
def iface():
	interface = TInterface('https://httpbin.org/')
	interface._ua.headers['Accept'] = '*/*'
	yield interface
	interface._ua.close()


class TestDeserialization:
	def test_json(self, iface):
		result = iface.json.get()
		assert 'slideshow' in result
		assert 'author' in result['slideshow']
	
	def test_html(self, iface):
		importorskip('pyquery',
				reason="HTML DOM deserialization depends on `pyquery` or installation with the `html` flag.")
		result = iface.html.get()
		assert len(result('h1')) == 1  # The sample coming back should have a singular heading.
	
	def test_xml(self, iface):
		result = iface.xml.get()
		assert result.tag == 'slideshow'
		assert 'author' in result.keys()
