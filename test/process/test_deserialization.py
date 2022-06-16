# It is often desirable to proactively catch errors being returned by third-party APIs.
# You can mix-in the Validated class to apply this behavior.

from pytest import fixture

from web.api.client import Interface
from web.api.processing import Serialized


class TInterface(Serialized, Interface): pass


@fixture
def iface():
	interface = TInterface('https://httpbin.org/')
	yield interface
	interface._ua.close()


class TestValidation:
	def test_html(self, iface):
		from pyquery import PyQuery
		
		result = iface.html.get()
		
		assert isinstance(result, PyQuery)
	
	def test_json(self, iface):
		result = iface.json.get()
		
		assert isinstance(result, dict)
		assert set(result['slideshow'].keys()) == {'author', 'date', 'title', 'slides'}
	
	def test_xml(self, iface):
		from xml.etree.ElementTree import Element
		
		result = iface.xml.get()
		
		assert isinstance(result, Element)
