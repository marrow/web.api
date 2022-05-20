"""Web-based API response processing.

This module provides mix-in classes to use to construct specialized Interface subclasses that utilize certain forms of
automatic response processing. The order in which you inherit determines the order of the processing pipeline.
"""

from marrow.package.loader import traverse


class Validated:
	def _process(self, response):
		response.raise_for_status()
		response = super()._process(response)
		
		return response


class Body:
	def _process(self, response):
		response = super()._process(response)
		return response.body


class Serialized:
	def _process(self, response):
		response = super()._process(response)
		# TODO: Actually negotiate. ;P
		return response.json()


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
	
	_success: str  # The path to a boolean indicating success if True.
	_failure: str  # The path to a boolean indicating failure if True.
	_message: str  # The path to the message returned representing a summary of the transaction.
	_content: str  # The path to the actual response content.
	
	def _process(self, response):
		result = super()._process(response)
		
		if self._success and not traverse(result, self._success) or self._failure and traverse(result, self._failure):
			raise ValueError("Request not successful.", extra={'message': traverse(result, self._message, None)})
		
		return traverse(result, self._content) if self._content else result

