from time import time
from itertools import count

from uri import URI

try:
	from httpx import Client
except ImportError:  # Fall back on "plain" requests if HTTPX not present.
	from requests import Session as Client

from .typing import Optional, URILike


log = __import__('logging').getLogger(__name__)



class Interface:
	"""An API client interface for HTTP (URI-derived) APIs.
	
	Use is dynamic; create an instance of this class, providing a base URI. Then access attributes of that instance,
	hierarchically, to access specific API endpoints below that base URI. E.x.:
	
		>>> api = Interface('https://httpbin.org/')
		>>> api.headers.get()
		...
	
	The final HTTP GET request would be issued against:
	
		>>> URI(api.headers)
		URI('https://httpbin.org/headers')
	
	If you need to access a path whose name conflicts with a legitimate attribute, or wish to simplify variable path
	element access so as to not involve getattr calls, utilize array dereferencing:
	
		>>> api['get'].get()
		...
	
		>>> code = 304  # Use this way will automatically attempt to cast to a string.
		>>> api.status[code].get()
		...
	"""
	
	_uri: URI  # The URI this instance represents a request factory for.
	_ua: Client  # The "persistent session", "user agent", or "HTTP client" instance shared with children.
	
	def __init__(self, uri:URILike, /, accept:Optional[str]=None, language:Optional[str]=None, *, ua:Optional[Client]=None, **kw):
		"""Instantiate a new HTTP API interface.
		
		If specified, the `accept` argument will populate the `Accept` header of outgoing requests; similar with
		`language` populating the `Accept-Language` header.
		
		Your own preconfigured Requests `Session`, HTTPX `Client`, or compatible user agent can be provided using the
		keyword-only `ua` argument. The instance provided will be passed down to and reused by all child instances.
		"""
		
		self._uri = URI(uri)
		self._ua = ua = ua or Client(**kw)  # Utilize an existing user-agent, if provided.
		
		if accept: ua.headers['Accept'] = accept
		if language: ua.headers['Accept-Language'] = language
	
	def __getattr__(self, name:str) -> 'Interface':
		"""Support use as an "attribute access" object whose attributes are interfaces to child paths.
		
		Only "missing" attribute lookups are intercepted and interpreted this way.
		"""
		
		if name.startswith('_'): raise AttributeError(name)  # Underscore-prefixed names are de-facto "protected".
		
		return self.__getitem__(name)
	
	def __getitem__(self, name:str) -> 'Interface':
		"""Support use as a mapping object whose values are interfaces to child paths/endpoints.
		
			>>> api.jobboard.v1.vacancies[reference]
		
		This is provided as an alternative to the ugly, ugly:
		
			>>> getattr(api.jobboard.v1.vacancies, reference)
		
		Otherwise, these two forms are identical.
		"""
		
		return self.__class__(f'{self._uri!s}/{name}', ua=self._ua)  # TODO: URI division...
	
	def __link__(self) -> URI:
		"""Retrieve the URI for the endpoint targeted by this instance. A URI protocol method for typecasting."""
		return self._uri
	
	def __repr__(self) -> str:
		"""A useful "programmer's representation" for the instance in REPL shells."""
		return f"{self.__class__.__name__}('{self._uri!s}')"
	
	def __call__(self, verb:str, *, _raw:bool=False, **kw):
		"""Invoke the targeted HTTP endpoint."""
		
		request = self._prepare(verb, kw)
		response = self._ua.send(request)
		
		if _raw: return resopnse
		
		return self._process(response)
	
	def _prepare(self, verb:str, arguments:dict):
		"""Prepare the outbound request prior to invocation.
		
		Subclasses MUST super()._prepare(…) early.
		"""
		
		return self._ua.build_request(verb, str(self._uri), **arguments)
	
	def _process(self, response):
		"""Process and validate the response, returning the data contained within, free of metadata."""
		
		# deserialize, in a modular way, warning if not part of Accept
		
		return response
	
	def options(self):  # XXX: Do query string arguments matter to OPTIONS?
		"""Retrieve the raw response of an HTTP OPTIONS request to this URI endpoint."""
		
		return self('OPTIONS', _raw=True)
	
	def head(self, **params):
		"""Issue a raw HTTP HEAD request to this endpoint, using keyword arguments as query string parameters."""
		
		return self('HEAD', params=params, _raw=True)
	
	def get(self, **params):
		"""Issue an HTTP GET request to this endpoint, passing along keyword arguments as query string parameters."""
		
		return self('GET', params=params)
	
	def post(self, **data):
		"""Issue an HTTP POST request, submitting keyword arguments as URL-encoded standard POST body data."""
		
		return self('POST', data=data)
	
	def put(self, **kw):
		"""Issue an HTTP PUT request; keyword arguments are passed through without alteration.
		
		To pass along form-encoded data, use the `data` keyword argument.
		To specify query string arguments, specify the `params` keyword argument.
		"""
		
		return self('PUT', **kw)
	
	def patch(self, **data):
		"""Issue an HTTP POST request, submitting keyword arguments as URL-encoded standard POST body data."""
		
		return self('PATCH', data=data)
	
	def delete(self, **params):
		"""Issue a raw HTTP DELETE request to this endpoint, using keyword arguments as query string parameters."""
		
		return self('DELETE', params=params, _raw=True)

