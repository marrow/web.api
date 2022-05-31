# An interface may be utilized as a context manager, permitting automatic actions to be performed at the beginning
# and end of a single "session".

from pytest import fixture

from web.api.client import Interface


class TInterface(Interface):
	def __init__(self, *args, **kw):
		super(TInterface, self).__init__(*args, **kw)
		
		self.entered = False
		self.authenticated = False
	
	def _authenticate(self):
		self.authenticated = True
		self._ua.headers['Cookie'] = 'test=42'  # Assign a cookie to the interface root.
	
	def _deauthenticate(self):
		self.authenticated = False
		self._ua.headers.pop('Cookie')
	
	def __enter__(self):
		self.entered = True
		return super(TInterface, self).__enter__()
	
	def __exit__(self, exc_type, exc_value, traceback):
		self.entered = False
		return super(TInterface, self).__exit__(exc_type, exc_type, traceback)


@fixture
def iface():
	return TInterface('https://httpbin.org/')


def test_context_management(iface):
	assert not iface.entered
	assert not iface.authenticated
	
	with iface:
		assert iface.entered
		assert iface.authenticated
		
		endpoint = iface.headers  # Descend into child resource.
		result = endpoint.get().json()  # Request this child resource.
		
		# Validate that the root session applied to the child request.
		assert 'Cookie' in result['headers']
		assert result['headers']['Cookie'] == 'test=42'
	
	assert not iface.entered
	assert not iface.authenticated
	
	# The underlying user agent / client will now be dead and can not be re-used.
	# This will impact all derived interface instances.
