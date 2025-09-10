import json
import time
from typing import Optional

import requests
from cdo_ai_modules.config.settings import load_config
from loguru import logger

from model.models import AuthResponse, ResourceStatusResponse, EventStatusResponse, DeviceStatusResponse, AuthParams


class RestApiClient:
    """A REST API client for the SAL troubleshooting MCP."""

    def __init__(self):
        """Initialize the client."""
        self._auth_token: Optional[AuthResponse] = None
        self._token_expiry_time: Optional[float] = None
        self.config = load_config()
        self.hostname = self.config["sal_client"]["hostname"]
        self.client_id = self.config["sal_client"]["client_id"]
        self.client_secret = self.config["sal_client"]["client_secret"]


    def _get_auth_token(self) -> str:
        """Get the auth token, refreshing if necessary."""
        if self._auth_token is None or (self._token_expiry_time and time.time() > self._token_expiry_time):
            self.login()
        
        if not self._auth_token:
            raise ConnectionError("Authentication failed, no token available.")
            
        return self._auth_token.access_token

    def login(self):
        """Authenticate and retrieve an auth token."""
        login_url = f"{self.hostname}/swc/v1/login"
        auth_params = AuthParams(
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        try:
            # Send JSON body (like Postman)
            response = requests.post(login_url, json=auth_params.model_dump())
            response.raise_for_status()
            self._auth_token = AuthResponse(**response.json())
            self._token_expiry_time = time.time() + self._auth_token.expires_in - 60  # 60s buffer
            logger.info("Successfully authenticated and got a new token.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_resource_status(self, stream_id: str) -> ResourceStatusResponse:
        """Get resource status."""
        url = f"{self.hostname}/swc/v1/troubleshoot/resource-status?stream_id={stream_id}"
        headers = {"Authorization": f"Bearer {self._get_auth_token()}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return ResourceStatusResponse(**response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get resource status: {e}")
            raise

    def get_event_status(self, stream_id: str) -> EventStatusResponse:
        """Get event status."""
        url = f"{self.hostname}/swc/v1/troubleshoot/events-status?stream_id={stream_id}"
        headers = {"Authorization": f"Bearer {self._get_auth_token()}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return EventStatusResponse(**response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get event status: {e}")
            raise

    def get_device_status(self, sse_id: str) -> DeviceStatusResponse:
        """Get device status."""
        url = f"{self.hostname}/swc/v1/troubleshoot/devices-status?sse_id={sse_id}"
        headers = {"Authorization": f"Bearer {self._get_auth_token()}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return DeviceStatusResponse(**response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get device status: {e}")
            raise