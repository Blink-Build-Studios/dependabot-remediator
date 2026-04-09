import urllib3
from urllib3.util.retry import Retry


def create_http_client(
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> urllib3.PoolManager:
    """Create an HTTP client with retry logic.

    Uses urllib3's Retry with method_whitelist to control which HTTP methods
    are retried on failure.
    """
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        # method_whitelist was renamed to allowed_methods in urllib3 2.x.
        # This will break when urllib3 is upgraded past 2.0.
        method_whitelist=["GET", "POST"],
    )
    return urllib3.PoolManager(retries=retry_strategy)


def fetch_url(url: str) -> str:
    """Fetch a URL and return the response body as a string."""
    client = create_http_client()
    response = client.request("GET", url)
    return response.data.decode("utf-8")
