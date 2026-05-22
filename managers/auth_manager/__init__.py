"""
Auth manager package.

Exports:
- get_client: builds an authenticated Coinbase RESTClient from a key file.
- auth_headers: returns headers with CB-PORTFOLIO-ID from env.
"""

from .auth_jwt import get_client, auth_headers

__all__ = ["get_client", "auth_headers"]
