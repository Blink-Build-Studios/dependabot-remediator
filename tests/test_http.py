from unittest.mock import patch

from myapp.http import create_http_client, fetch_url


class TestCreateHttpClient:
    """Tests for the HTTP client factory."""

    def test_creates_pool_manager(self) -> None:
        """Should return a configured PoolManager."""
        import urllib3

        client = create_http_client()
        assert isinstance(client, urllib3.PoolManager)

    def test_default_retry_count(self) -> None:
        """Default retry strategy should have 3 retries."""
        client = create_http_client()
        retry = client.connection_pool_kw.get("retries")
        assert retry is not None
        assert retry.total == 3

    def test_custom_retry_count(self) -> None:
        """Custom retry count should be respected."""
        client = create_http_client(retries=5)
        retry = client.connection_pool_kw.get("retries")
        assert retry.total == 5

    def test_retry_methods(self) -> None:
        """Retry should be configured for GET and POST methods."""
        client = create_http_client()
        retry = client.connection_pool_kw.get("retries")
        # In urllib3 1.x this is method_whitelist, in 2.x it's allowed_methods
        methods = getattr(retry, "method_whitelist", None) or getattr(retry, "allowed_methods", None)
        assert methods is not None
        assert "GET" in methods
        assert "POST" in methods


class TestFetchUrl:
    """Tests for the fetch_url helper."""

    @patch("myapp.http.create_http_client")
    def test_fetch_url_returns_decoded_body(self, mock_create_client: object) -> None:
        """Should return the response body decoded as UTF-8."""
        mock_response = type("MockResponse", (), {"data": b"Hello, world!"})()
        mock_client = mock_create_client.return_value
        mock_client.request.return_value = mock_response

        result = fetch_url("https://example.com")

        assert result == "Hello, world!"
        mock_client.request.assert_called_once_with("GET", "https://example.com")
