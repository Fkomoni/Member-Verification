"""
Prognosis Provider Authentication — adapter for /api/ProviderNetwork/ProviderLogIn.

Flow:
  1. Get system Bearer token via /api/ApiUsers/Login (cached, auto-refresh)
  2. Call /api/ProviderNetwork/ProviderLogIn with Bearer + provider email/password
  3. On success: upsert provider in local DB, return local JWT
  4. On failure: return 401

The system token is already handled by prognosis_client._get_prognosis_token().
This module adds the provider-level login on top.

Response shape assumed (will adjust when live response is confirmed):
{
  "status": "success",
  "providerId": "...",
  "providerName": "...",
  "facilityName": "...",
  "email": "...",
  ...
}
"""

import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)

# Reuse the system token from prognosis_client
from app.services.prognosis_client import _get_prognosis_token


async def authenticate_provider(email: str, password: str) -> dict | None:
    """
    Authenticate a provider against the Prognosis ProviderLogIn endpoint.

    Returns provider data dict on success, None on failure.
    """
    if not settings.PROGNOSIS_BASE_URL:
        log.warning("PROGNOSIS_BASE_URL not configured — cannot authenticate provider")
        return None

    # Step 1: Get system token
    system_token = await _get_prognosis_token()
    if not system_token:
        log.error("Cannot get system token for provider auth")
        return None

    # Step 2: Call ProviderLogIn
    url = f"{settings.PROGNOSIS_BASE_URL}/api/ProviderNetwork/ProviderLogIn"
    headers = {
        "Authorization": f"Bearer {system_token}",
        "Content-Type": "application/json",
    }
    payload = {"email": email, "password": password}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            log.info("Prognosis provider login success for %s", email)
            return data
        elif resp.status_code == 401:
            # Maybe system token expired — retry once
            from app.services.prognosis_client import _prognosis_token_expiry
            import app.services.prognosis_client as pc
            pc._prognosis_token_expiry = 0
            system_token = await _get_prognosis_token()
            if system_token:
                headers["Authorization"] = f"Bearer {system_token}"
                async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
            log.warning("Provider login failed for %s: 401 after token refresh", email)
            return None
        else:
            log.warning("Provider login failed for %s: status=%d body=%s",
                        email, resp.status_code, resp.text[:300])
            return None
    except httpx.RequestError as e:
        log.error("Provider login request failed: %s", e)
        return None
