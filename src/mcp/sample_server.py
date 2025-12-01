from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Optional
import os

# Load environment variables from a .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None  # type: ignore
else:
    try:
        load_dotenv()  # type: ignore
    except Exception:
        pass
from dotenv import load_dotenv

load_dotenv()

try:
    import requests
except ImportError as exc:
    requests = None  # type: ignore
    _requests_import_error = exc
else:
    _requests_import_error = None

mcp = FastMCP("SampleServer")


def _require_requests() -> None:
    if requests is None:
        raise RuntimeError(
            "The 'requests' package is required for IAM API calls. Please install it (e.g., pip install requests)."
        )


def _fetch_kavach_token(
    base_url: str,
    realm: str,
    username: str,
    password: str,
    client_id: str,
    client_secret: str,
    scope: str = "openid",
) -> str:
    _require_requests()
    token_url = f"{base_url}/realms/{realm}/protocol/openid-connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "username": username,
        "password": password,
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    response = requests.post(token_url, headers=headers, data=data, timeout=15)
    if response.status_code != 200:
        raise RuntimeError(f"Kavach token request failed: {response.status_code} {response.text}")
    payload = response.json()
    if "access_token" not in payload:
        raise RuntimeError("Kavach token response missing 'access_token'.")
    return payload["access_token"]


def _create_kavach_user(
    base_url: str,
    realm: str,
    bearer_token: str,
    user_payload: Dict,
) -> int:
    _require_requests()
    url = f"{base_url}/admin/realms/{realm}/users"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {bearer_token}",
        "content-type": "application/json",
    }
    response = requests.post(url, headers=headers, json=user_payload, timeout=15)
    return response.status_code


 


@mcp.tool()
def create_iam_user_with_token_fetch(
    email: str,
    first_name: str,
    last_name: str,
    username: Optional[str] = None,
    base_url: str = "http://192.168.1.9:8080",
    realm: str = "master",
    admin_username: str = "admin",
    admin_password: str = "admin",
    client_id: str = "admin-cli",
    client_secret: Optional[str] = None,
    email_verified: bool = True,
    enabled: bool = True,
    required_actions: Optional[List[str]] = None,
    groups: Optional[List[str]] = None,
    attributes: Optional[Dict[str, str]] = None,
) -> str:
    """Two-step: fetch Kavach token using client_secret, then create the user.

    This is equivalent to calling get_kavach_token followed by create_iam_user with bearer_token.
    """
    resolved_client_secret = client_secret or os.getenv("KAVACH_CLIENT_SECRET")
    if not resolved_client_secret:
        raise ValueError("client_secret required (or set KAVACH_CLIENT_SECRET)")

    token = _fetch_kavach_token(
        base_url=base_url,
        realm=realm,
        username=admin_username,
        password=admin_password,
        client_id=client_id,
        client_secret=resolved_client_secret,
    )

    # Derive username from email if not provided
    if not username:
        username = email.split("@")[0] if "@" in email else email

    user_payload = {
        "username": username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "emailVerified": email_verified,
        "enabled": enabled,
        "requiredActions": required_actions or ["UPDATE_PASSWORD"],
        "groups": groups or [],
        "attributes": attributes or {},
    }

    status_code = _create_kavach_user(
        base_url=base_url,
        realm=realm,
        bearer_token=token,
        user_payload=user_payload,
    )

    if status_code == 201:
        return "User created (201)."
    if status_code == 409:
        return "User already exists (409)."
    return f"User creation returned status {status_code}."

if __name__ == "__main__":
    mcp.run(transport="stdio")
