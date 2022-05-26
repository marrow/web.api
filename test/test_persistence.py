# A single Interface should persist the underlying "user agent" client between requests.
# This impacts "user agent" side-effects such as cookie persistence, often required to maintain authentication.


class TestPersistence:
	def test_cookie(self, iface):
		iface._ua.headers['Cookie'] = 'test=42'  # Assign a cookie to the interface root.
		endpoint = iface.headers  # Descend into child resource.
		result = endpoint.get().json()  # Request this child resource.
		
		# Validate that the root session applied to the child request.
		assert 'Cookie' in result['headers']
		assert result['headers']['Cookie'] == 'test=42'
