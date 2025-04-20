"""
API Package

This package provides a modular API system for the AI automation platform.
"""

from .api_manager import APIManager
from .api_utils import APIClient
from .base_api import BaseAPI

# Create a singleton API manager instance
api_manager = APIManager()

__all__ = ['APIManager', 'APIClient', 'BaseAPI', 'api_manager']