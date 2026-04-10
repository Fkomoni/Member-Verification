"""
Prognosis Provider Authentication — adapter for /api/ProviderNetwork/ProviderLogIn.

Flow:
  1. Get system Bearer token via /api/ApiUsers/Login (cached, auto-refresh)
  2. Call /api/ProviderNetwork/ProviderLogIn with Bearer + provider Email/Password
  3. On success: return provider data for local DB upsert
  4. On failure: return None (caller falls back to local DB)

Response shape:
{
  "status": 200,
  "result": [{ "provider_id": 8325, "surname": "...", "Email": "...", "ProviderStatus": "ACTIVE", ... }],
  "ErrorMessage": ""
}
"""

import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


async def _get_system_token() -> str | None:
    """Get system Bearer token from Prognosis. Reuses cached token from prognosis_client."""
    try:
        from app.services.prognosis_client import _get_prognosis_token
        return await _get_prognosis_token()
    except Exception as e:
        log.error("Failed to get system token: %s", e)
        return None


async def _refresh_system_token() -> str | None:
    """Force refresh the system token."""
    try:
        import app.services.prognosis_client as pc
        pc._prognosis_token_expiry = 0
        return await _get_system_token()
    except Exception as e:
        log.error("Failed to refresh system token: %s", e)
        return None


async def authenticate_provider(email: str, password: str) -> dict | None:
    """
    Authenticate a provider against the Prognosis ProviderLogIn endpoint.
    Returns provider data dict on success, None on failure.
    """
    base_url = settings.PROGNOSIS_BASE_URL.rstrip("/")
    if not base_url:
        log.warning("PROGNOSIS_BASE_URL not configured")
        return None

    # Step 1: Get system token
    system_token = await _get_system_token()
    if not system_token:
        log.error("Cannot get system token for provider auth")
        return None

    # Step 2: Call ProviderLogIn
    url = f"{base_url}/api/ProviderNetwork/ProviderLogIn"
    payload = {"Email": email, "Password": password}

    result = await _call_provider_login(url, system_token, payload)

    # If 401, refresh token and retry once
    if result == "RETRY":
        log.info("Retrying provider login after token refresh for %s", email)
        system_token = await _refresh_system_token()
        if system_token:
            result = await _call_provider_login(url, system_token, payload)

    if isinstance(result, dict):
        log.info("Prognosis provider login success for %s", email)
        return result

    log.warning("Prognosis provider login failed for %s", email)
    return None


async def _call_provider_login(url: str, token: str, payload: dict) -> dict | str | None:
    """
    Make the actual HTTP call. Returns:
    - dict: success (provider data)
    - "RETRY": got 401, should retry with fresh token
    - None: failed
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(url, json=payload, headers=headers)

        log.info("ProviderLogIn response: status=%d", resp.status_code)

        if resp.status_code == 200:
            data = resp.json()
            # Response: {"status": 200, "result": [...], "ErrorMessage": ""}
            result_list = data.get("result") or data.get("Result") or []
            error_msg = data.get("ErrorMessage") or data.get("errorMessage") or ""

            if error_msg:
                log.warning("ProviderLogIn API error: %s", error_msg)
                return None

            if isinstance(result_list, list) and len(result_list) > 0:
                return data

            log.warning("ProviderLogIn returned empty result")
            return None

        elif resp.status_code == 401:
            return "RETRY"

        else:
            log.warning("ProviderLogIn failed: %d %s", resp.status_code, resp.text[:300])
            return None

    except httpx.RequestError as e:
        log.error("ProviderLogIn request error: %s", e)
        return None
