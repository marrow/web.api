"""Web-based API response processing.

This module provides mix-in classes to use to construct specialized Interface subclasses that utilize certain forms of
automatic response processing. The order in which you inherit determines the order of the processing pipeline.
"""

from pkg_resources import Distribution, UnknownExtra, DistributionNotFound
from typing import Any, Callable, Mapping, Optional
from xml.etree import ElementTree as ET

from typeguard import check_argument_types

from marrow.package.host import PluginManager
from marrow.package.loader import traverse
from web.api.typing import Deserializer

try:
	from httpx import Request, Response
except ImportError:  # Fall back on "plain" requests if HTTPX not present.
	from requests import Request, Response


log = __import__('logging').getLogger(__name__)


class SafePluginManager(PluginManager):
	def _register(self, dist:Distribution) -> None:
		assert check_argument_types()
		entries = dist.get_entry_map(self.namespace)
		
		if not entries:
			return
		
		for name in entries:
			try:
				plugin = entries[name].load()
			
			except (UnknownExtra, DistributionNotFound):  # pragma: no cover
				log.warning("Skipping registration of '{!r}' due to missing dependencies.".format(dist), exc_info=True)
			
			except ImportError:  # pragma: no cover
				log.error("Skipping registration of '{!r}' due to error on import.".format(dist), exc_info=True)


class Validated:
	"""Validate the HTTP response status code."""
	
	def _process(self, request:Request, response:Response) -> Response:
		assert check_argument_types()
		
		response.raise_for_status()
		response = super()._process(request, response)
		
		return response


class Body:
	"""Retrieve only the binary body of the response."""
	
	def _process(self, request:Request, response:Response) -> bytes:
		assert check_argument_types()
		
		response = super()._process(request, response)
		return response.content


class Text:
	"""Retrieve only the textual body content of the response."""
	
	def _process(self, request:Request, response:Response) -> str:
		assert check_argument_types()
		
		response = super()._process(request, response)
		return response.text


class Serialized(Text):
	"""Automatically process serialized responses by de-serializing them to native Python objects.
	
	Utilizes content-type-based plugin loading via standard entry_points in the `web.deserialize` namespace.
	"""
	
	_loads = SafePluginManager('web.deserialize')
	
	def _process(self, request:Request, response:Response) -> Any:  # Can theoretically return any serialized type.
		assert check_argument_types()
		
		mime: str = response.headers['Content-Type'].partition(';')[0]
		loads: Deserializer = self._loads[mime]
		
		response = super()._process(request, response)
		
		if not response:
			return response
		
		return loads(response)


class Envelope(Serialized):
	"""Take a de-serialized response and process it as a combination of metadata and actual data.
	
	Verifies the "successful" nature of the response by looking for a key that must be truthy to indicate success, or
	one that if truthy indicates failure, or both. The actual data is then extracted from the result and passed along.
	
	This accommodates several response styles. Explicit success:
	
		{'success': True, …}
	
	Explicit failure, optionally with a message:
	
		{'state': {'failure': True, 'message': "Goofed."}}
	
	Explicit failure where the presence of the message is the indicator:
	
		{'error': "Something went wrong.", …}
	
	If no `_content` key path is provided the whole de-serialized response is returned and this only validates.
	"""
	
	# Override these attributes in subclasses.
	_success: Optional[str] = None  # The path to a boolean indicating success if present and truthy.
	_failure: Optional[str] = None  # The path to a boolean indicating failure if present and truthy.
	_message: Optional[str] = None  # The path to the message returned representing a summary of the transaction.
	_content: Optional[str] = None  # The path to the actual response content.
	
	def _process(self, request:Request, response:Mapping):
		"""Process the response, validate 'envelope' metadata, and extract wrapped content."""
		
		assert check_argument_types()  # Must have been de-serialized prior to reaching us.
		
		result = super()._process(request, response)
		
		if self._success and not traverse(result, self._success) or self._failure and traverse(result, self._failure):
			raise ValueError("Request not successful.", extra={'message': traverse(result, self._message, None)})
		
		return traverse(result, self._content) if self._content else result
