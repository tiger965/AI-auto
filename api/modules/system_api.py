"""
System API Module

Provides API access to system-level operations and monitoring.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, List, Any, Optional
import platform
import psutil

from config import config
from api.base_api import BaseAPI

class SystemAPI(BaseAPI):
    """API module for system operations"""
    
    def __init__(self):
        """Initialize the system API module"""
        super().__init__()
        self.name = "system"
        self.description = "System operations and monitoring API endpoints"
        self.version = "1.0.0"
        self.route_prefix = f"/api/{self.name}"
    
    def register_endpoints(self, bp: Blueprint) -> None:
        """
        Register system API endpoints
        
        Args:
            bp: Flask blueprint
        """
        @bp.route('/info', methods=['GET'])
        def system_info():
            """Get system information"""
            try:
                system_info = {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node(),
                    "processor": platform.processor()
                }
                return jsonify(system_info)
            except Exception as e:
                self.logger.error(f"Error getting system info: {e}")
                return jsonify({"error": str(e)}), 500
        
        @bp.route('/resources', methods=['GET'])
        def system_resources():
            """Get system resource usage"""
            try:
                resources = {
                    "cpu": {
                        "percent": psutil.cpu_percent(interval=0.1),
                        "count": psutil.cpu_count()
                    },
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "percent": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "total": psutil.disk_usage('/').total,
                        "free": psutil.disk_usage('/').free,
                        "percent": psutil.disk_usage('/').percent
                    }
                }
                return jsonify(resources)
            except Exception as e:
                self.logger.error(f"Error getting system resources: {e}")
                return jsonify({"error": str(e)}), 500
                
        @bp.route('/services', methods=['GET'])
        def get_services():
            """Get status of system services"""
            services = {
                "api": True,
                "knowledge_core": config.get("modules.knowledge_core.enabled", True),
                "training_local": config.get("modules.training_local.enabled", True),
                "repair_backup": config.get("modules.repair_backup.enabled", True)
            }
            return jsonify(services)
    
    def get_endpoints_info(self) -> List[Dict[str, str]]:
        """
        Get information about available endpoints
        
        Returns:
            List of endpoint information dictionaries
        """
        # Get basic endpoints from parent class
        endpoints = super().get_endpoints_info()
        
        # Add system-specific endpoints
        endpoints.extend([
            {
                "path": f"{self.route_prefix}/info",
                "method": "GET",
                "description": "Get system information"
            },
            {
                "path": f"{self.route_prefix}/resources",
                "method": "GET",
                "description": "Get system resource usage"
            },
            {
                "path": f"{self.route_prefix}/services",
                "method": "GET",
                "description": "Get status of system services"
            }
        ])
        
        return endpoints