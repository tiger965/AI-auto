"""
Base API Module

Provides the base class for all API modules.
"""

import logging
from typing import Dict, List, Any, Optional
from flask import Blueprint, jsonify


class BaseAPI:
    """Base class for API modules"""

    def __init__(self):
        """Initialize the base API"""
        self.logger = logging.getLogger(__name__)
        self.name = "base"  # Override in subclasses
        self.description = "Base API module"  # Override in subclasses
        self.version = "1.0.0"  # Override in subclasses
        self.route_prefix = f"/api/{self.name}"

    def create_blueprint(self) -> Blueprint:
        """
        Create a Flask blueprint for this API module

        Returns:
            Blueprint: Flask blueprint
        """
        bp = Blueprint(self.name, __name__, url_prefix=self.route_prefix)

        # Add default info endpoint
        @bp.route("/info", methods=["GET"])
        def info():
            return jsonify(
                {
                    "module": self.name,
                    "description": self.description,
                    "version": self.version,
                    "endpoints": self.get_endpoints_info(),
                }
            )

        # Register module-specific endpoints
        self.register_endpoints(bp)

        return bp

    def register_endpoints(self, blueprint: Blueprint) -> None:
        """
        Register endpoints on the blueprint

        Args:
            blueprint: Flask blueprint
        """
        # Override in subclasses to add specific endpoints
        pass

    def get_endpoints_info(self) -> List[Dict[str, str]]:
        """
        Get information about available endpoints

        Returns:
            List of endpoint information dictionaries
        """
        # Basic endpoint info - override in subclasses to add more
        return [
            {
                "path": f"{self.route_prefix}/info",
                "method": "GET",
                "description": "Get information about this API module",
            }
        ]