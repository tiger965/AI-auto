"""
Knowledge API Module

Provides API access to the knowledge module functionality.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional

from config import config
from api.base_api import BaseAPI


class KnowledgeAPI(BaseAPI):
    """API module for knowledge functionality"""

    def __init__(self):
        """Initialize the knowledge API module"""
        super().__init__()
        self.name = "knowledge"
        self.description = "Knowledge system API endpoints"
        self.version = "1.0.0"
        self.route_prefix = f"/api/{self.name}"

        # Check if knowledge module is enabled
        self.enabled = config.get("modules.knowledge_core.enabled", True)

    def register_endpoints(self, bp: Blueprint) -> None:
        """
        Register knowledge API endpoints

        Args:
            bp: Flask blueprint
        """

        @bp.route("/status", methods=["GET"])
        def knowledge_status():
            """Get knowledge module status"""
            return jsonify(
                {
                    "enabled": self.enabled,
                    "database_path": config.get(
                        "modules.knowledge_core.database_path", "data/knowledge.db"
                    ),
                    "entry_count": self._get_entry_count(),
                }
            )

        @bp.route("/entries", methods=["GET"])
        def get_entries():
            """Get knowledge entries"""
            if not self.enabled:
                return jsonify({"error": "Knowledge module is disabled"}), 503

            # Optional filter parameter
            query = request.args.get("query", "")
            limit = int(request.args.get("limit", 100))

            entries = self._get_entries(query, limit)
            return jsonify({"entries": entries})

        @bp.route("/entries", methods=["POST"])
        def add_entry():
            """Add a knowledge entry"""
            if not self.enabled:
                return jsonify({"error": "Knowledge module is disabled"}), 503

            data = request.json
            if not data or "key" not in data or "value" not in data:
                return jsonify({"error": "Missing required fields (key, value)"}), 400

            success = self._add_entry(data["key"], data["value"])
            if success:
                return jsonify({"status": "success"}), 201
            else:
                return jsonify({"error": "Failed to add entry"}), 500

    def get_endpoints_info(self) -> List[Dict[str, str]]:
        """
        Get information about available endpoints

        Returns:
            List of endpoint information dictionaries
        """
        # Get basic endpoints from parent class
        endpoints = super().get_endpoints_info()

        # Add knowledge-specific endpoints
        endpoints.extend(
            [
                {
                    "path": f"{self.route_prefix}/status",
                    "method": "GET",
                    "description": "Get knowledge module status",
                },
                {
                    "path": f"{self.route_prefix}/entries",
                    "method": "GET",
                    "description": "Get knowledge entries",
                },
                {
                    "path": f"{self.route_prefix}/entries",
                    "method": "POST",
                    "description": "Add a knowledge entry",
                },
            ]
        )

        return endpoints

    def _get_entry_count(self) -> int:
        """
        Get count of knowledge entries

        Returns:
            Number of entries
        """
        # This would normally access the knowledge module
        # but for now, return a placeholder value
        return 0

    def _get_entries(self, query: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get knowledge entries

        Args:
            query: Search query
            limit: Maximum number of entries to return

        Returns:
            List of entries
        """
        # This would normally access the knowledge module
        # but for now, return placeholder data
        return []

    def _add_entry(self, key: str, value: Any) -> bool:
        """
        Add a knowledge entry

        Args:
            key: Entry key
            value: Entry value

        Returns:
            Success status
        """
        # This would normally access the knowledge module
        # but for now, return success
        return True