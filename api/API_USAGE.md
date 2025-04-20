# API Usage Guide

This document provides instructions and examples for using the AI Automation System API.

## Table of Contents

1. [Overview](#overview)
2. [API Client Usage](#api-client-usage)
3. [Available API Modules](#available-api-modules)
4. [Authentication](#authentication)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

## Overview

The AI Automation System provides a RESTful API for interacting with various system components. The API is modular, with different modules providing specific functionality:

- **Core API**: System-level operations and configuration
- **Knowledge API**: Knowledge base management
- **Training API**: Model training and management
- **System API**: System monitoring and services

## API Client Usage

The system provides a built-in API client that can be used to interact with the API programmatically:

```python
from api import APIClient

# Create an API client
client = APIClient()

# Get system status
status = client.get("core/status")
print(f"System status: {status}")

# Add a knowledge entry
result = client.post("knowledge/entries", json={
    "key": "example_key",
    "value": "example_value"
})