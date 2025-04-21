"""
API Utilities

Provides utility functions and classes for API operations.
"""

import logging
import requests
from typing import Dict, Any, Optional
from config import config


class APIClient:
    """Client for making API requests"""

    def __init__(self, base_url: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize the API client

        Args:
            base_url: Base URL for API requests (default from config)
            port: Port for API requests (default from config)
        """
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url or config.get("api.host", "localhost")
        self.port = port or config.get("api.port", 5000)
        self.timeout = config.get("api.timeout", 10)

        # Construct the API URL
        self.api_url = f"http://{self.base_url}:{self.port}"
        self.logger.info(f"Initialized API client with URL: {self.api_url}")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Making GET request to {url}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()  # Raise exception for error status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request to the API

        Args:
            endpoint: API endpoint path
            data: Form data
            json: JSON data

        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Making POST request to {url}")
            response = requests.post(
                url, data=data, json=json, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request to the API

        Args:
            endpoint: API endpoint path
            data: Form data
            json: JSON data

        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Making PUT request to {url}")
            response = requests.put(
                url, data=data, json=json, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {"error": str(e)}

    def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a DELETE request to the API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            self.logger.debug(f"Making DELETE request to {url}")
            response = requests.delete(
                url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return {"error": str(e)}