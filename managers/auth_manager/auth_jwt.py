# v1.1.1
"""
auth_manager / auth_jwt

Public API
- get_client(key_file_env: str = "COINBASE_KEY_FILE") -> RESTClient
- auth_headers(pfid_env: str = "PFID") -> dict

Contract
- PFID is sent in headers only (CB-PORTFOLIO-ID).
- Env-only: PFID and COINBASE_KEY_FILE. No hardcoding. No prompts.
- No globals. No caching. No side effects beyond constructing the client.
- Clear exceptions on missing/blank envs and missing key file.
v1.1.1: Repair. Reinstall v1.1.0 implementation. Attach PFID header at client construction.
"""
import os
import os.path
import logging
from coinbase.rest import RESTClient


def _read_required_env(name: str) -> str:
    """Return trimmed env value or raise ValueError if missing/blank."""
    val = os.environ.get(name, "")
    val = val.strip() if isinstance(val, str) else ""
    if not val:
        raise ValueError(f"Missing env {name}")
    return val


def _attach_pfid_header(client, pfid) -> bool:
    """
    Best-effort attach of the CB-PORTFOLIO-ID header to the underlying client.
    Tries, in order: client.session.headers, client._session.headers, client.default_headers.
    Returns True if attached; otherwise False. Never raises. Does not log secrets.
    """
    try:
        if not pfid:
            return False
        header = {"CB-PORTFOLIO-ID": pfid}

        # a) requests-like session
        if hasattr(client, "session") and hasattr(getattr(client, "session", None), "headers"):
            headers_obj = getattr(client.session, "headers", None)
            if hasattr(headers_obj, "update"):
                headers_obj.update(header)
                logging.getLogger(__name__).info("[AUTH] PFID header attached")
                return True

        # b) private session
        if hasattr(client, "_session") and hasattr(getattr(client, "session", None), "headers"):
            headers_obj = getattr(client._session, "headers", None)
            if hasattr(headers_obj, "update"):
                headers_obj.update(header)
                logging.getLogger(__name__).info("[AUTH] PFID header attached")
                return True

        # c) default headers dict
        if hasattr(client, "default_headers"):
            default_headers = getattr(client, "default_headers")
            if isinstance(default_headers, dict):
                default_headers.update(header)
                logging.getLogger(__name__).info("[AUTH] PFID header attached")
                return True

        # d) else: no-op
        return False
    except Exception:
        # Best-effort only; never fail client construction on header attach.
        return False


def get_client(key_file_env: str = "COINBASE_KEY_FILE") -> RESTClient:
    """
    Build and return a Coinbase RESTClient using the key file path in env.

    Raises
    - ValueError: when the env is missing or blank.
    - FileNotFoundError: when the path does not point to a file.
    """
    key_path = _read_required_env(key_file_env)
    if not os.path.isfile(key_path):
        raise FileNotFoundError(f"Key file not found: {key_path}")
    client = RESTClient(key_file=key_path)
    # Attach PFID header at construction so all requests include it by default.
    pfid = os.environ.get("PFID")
    _attach_pfid_header(client, pfid)
    return client


def auth_headers(pfid_env: str = "PFID") -> dict:
    """
    Return the headers dict with CB-PORTFOLIO-ID set from env.

    Raises
    - ValueError: when the env is missing or blank.
    """
    pfid = _read_required_env(pfid_env)
    return {"CB-PORTFOLIO-ID": pfid}
