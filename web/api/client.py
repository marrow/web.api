from time import time
from itertools import count

from uri import URI

try:
	from httpx import Client, Request, Request as PreparedRequest, Response
except ImportError:  # Fall back on "plain" requests if HTTPX not present.
	from requests import Session as Client, Request, PreparedRequest, Response

from .typing import ExcType, ExcValue, Optional, Trace, URILike


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
	
	_sane: bool = True  # The remote API utilizes HTTP status codes in a sane way.
	_uri: URI  # The URI this instance represents a request factory for.
	_ua: Client  # The "persistent session", "user agent", or "HTTP client" instance shared with children.
	
	def __init__(self, uri:URILike, /, accept:Optional[str]=None, language:Optional[str]=None, *,
			ua:Optional[Client]=None, **kw):
		"""Instantiate a new HTTP API interface.
		
		If specified, the `accept` argument will populate the `Accept` header of outgoing requests; similar with
		`language` populating the default `Accept-Language` header. These may be overridden per-request by supplying
		alternative `headers`.
		
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
	
	def __call__(self, verb:str, *, _raw:bool=False, **kw):  # Return not defined as subclass _process may mutate.
		"""Invoke the targeted HTTP endpoint."""
		
		self._authenticate()
		request = self._prepare(verb, kw)
		response = self._ua.send(request)
		
		if _raw: return response
		
		return self._process(request, response)
	
	# Context (Connection) Management
	
	def __enter__(self) -> 'Interface':
		"""Utilize Python's "context manager" functionality as a form of session state."""
		self._ua.__enter__()  # The upstream HTTPX or Requests session/client returns self.
		self._authenticate()  # Perform authentication as part of "session establishment" entering the context.
		return self
	
	def __exit__(self, exc_type:ExcType, exc_value:ExcValue, traceback:Trace):
		"""De-authenticate as needed and automatically close any hanging HTTP server connections."""
		self._deauthenticate()  # Perform the inverse of logging in when exiting the context.
		self._ua.__exit__(exc_type, exc_value, traceback)
	
	# Access Control / Authentication / Authorization
	
	def _authenticate(self):
		"""Perform any requests or configuration required to authenticate or authorize subsequent requests.
		
		To prevent unintentional infinite recursion, requests issued within this method should be submitted by way of
		`self._ua` directly. It is the responsibility of the Interface specialization or mix-in implementing this to
		identify if authentication is *actually* required as this method will be called prior to every request.
		"""
		
		pass
	
	def _deauthenticate(self):
		"""Perform the cleanup work or issue a request required to de-authenticate."""
		
		pass
	
	# Request/Response Lifecycle Processing
	
	def _prepare(self, verb:str, arguments:dict) -> PreparedRequest:
		"""Prepare the outbound request prior to invocation.
		
		Subclasses MUST super()._prepare(…) early.
		"""
		
		return self._ua.build_request(verb, str(self._uri), **arguments)
	
	def _process(self, request:Request, response:Response):  # As per __call__ itself, may free of encapsulation.
		"""Process and validate the response, returning the data contained within, free of metadata."""
		
		# De-serialize, in a modular way, warning if not part of the original Accept.
		
		if self._sane: response.raise_for_status()
		
		return response
	
	# HTTP Verbs
	
	def options(self):  # XXX: Do query string arguments matter to OPTIONS?
		"""Retrieve the raw response of an HTTP OPTIONS request to this URI endpoint."""
		
		return self('OPTIONS', _raw=True)
	
	def head(self, **params) -> Response:
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
	
	def delete(self, **params) -> Response:
		"""Issue a raw HTTP DELETE request to this endpoint, using keyword arguments as query string parameters."""
		
		return self('DELETE', params=params, _raw=True)
