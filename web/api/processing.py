"""Web-based API response processing.

This module provides mix-in classes to use to construct specialized Interface subclasses that utilize certain forms of
automatic response processing. The order in which you inherit determines the order of the processing pipeline.
"""

from typing import Mapping, Optional

from typeguard import check_argument_types

from marrow.package.host import PluginManager
from marrow.package.loader import traverse

try:
	from httpx import Request, Response
except ImportError:  # Fall back on "plain" requests if HTTPX not present.
	from requests import Request, Response


class Validated:
	"""Validate the HTTP response status code."""
	
	def _process(self, request:Request, response:Response):
		assert check_argument_types()
		
		response.raise_for_status()
		response = super()._process(request, response)
		
		return response


class Body:
	"""Retrieve only the body of the response."""
	
	def _process(self, request:Request, response:Response) -> str:
		assert check_argument_types()
		
		response = super()._process(request, response)
		return response.body


class Serialized:
	"""Automatically process serialized responses by de-serializing them to native Python objects.
	
	Utilizes content-type-based plugin loading via standard entry_points in the `web.deserialize` namespace.
	"""
	
	_loads = PluginManager('web.deserialize')
	
	def _process(self, request:Request, response:Response):  # Can theoretically return any serialized type.
		assert check_argument_types()
		
		response = super()._process(request, response)
		
		mime: str = req.content_type.partition(';')[0]
		loads: Deserializer = self._loads[mime]
		
		return loads(response.text())


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

