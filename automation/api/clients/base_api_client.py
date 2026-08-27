import requests
from typing import Dict, Any, Optional
from automation.configuration.config import Config
from automation.utilities.logger import get_logger

logger = get_logger("APIClient")


class BaseAPIClient:
    """Base REST API client handling sessions, token authentication, and status code assertions."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def set_auth_token(self, token: str) -> None:
        """Sets Bearer token for authorized API requests."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_auth_token(self) -> None:
        """Removes Bearer token header."""
        self.session.headers.pop("Authorization", None)

    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Sends an HTTP request and logs details."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        logger.info(f"API Request: {method.upper()} {url}")

        response = self.session.request(
            method=method,
            url=url,
            data=data,
            json=json,
            params=params,
            headers=headers
        )

        logger.info(f"API Response: Status {response.status_code} ({len(response.content)} bytes)")
        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
