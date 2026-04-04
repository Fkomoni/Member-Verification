"""
Client for integrating with the Prognosis (Leadway Health) core HMO system.

Authentication:
  POST /api/ApiUsers/Login → returns JWT token
  Then use token for:
  GET /api/ProviderNetwork/ValidateEnrolleeProviderAccessList
      ?cifno={enrollee_cif}&providerid={provider_id}
"""

import logging
import time

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)

# Cache the Prognosis auth token (expires after ~50 min, refresh at 45)
_prognosis_token: str | None = None
_prognosis_token_expiry: float = 0
_TOKEN_REFRESH_SECONDS = 45 * 60  # refresh every 45 minutes


async def _get_prognosis_token() -> str | None:
    """
    Authenticate with Prognosis API and cache the token.
    POST /api/ApiUsers/Login
    """
    global _prognosis_token, _prognosis_token_expiry

    # Return cached token if still valid
    if _prognosis_token and time.time() < _prognosis_token_expiry:
        return _prognosis_token

    if not settings.PROGNOSIS_BASE_URL:
        log.warning("PROGNOSIS_BASE_URL not configured")
        return None

    url = f"{settings.PROGNOSIS_BASE_URL}/api/ApiUsers/Login"
    payload = {
        "Username": settings.PROGNOSIS_USERNAME,
        "Password": settings.PROGNOSIS_PASSWORD,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(url, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            # The token might be in data directly or in a "token" field
            if isinstance(data, str):
                _prognosis_token = data
            elif isinstance(data, dict):
                _prognosis_token = data.get("token") or data.get("Token") or data.get("access_token")
            else:
                _prognosis_token = str(data)

            _prognosis_token_expiry = time.time() + _TOKEN_REFRESH_SECONDS
            log.info("Prognosis authentication successful")
            return _prognosis_token
        else:
            log.error("Prognosis login failed: status=%d body=%s", resp.status_code, resp.text[:200])
            return None
    except httpx.RequestError as e:
        log.error("Prognosis login request failed: %s", e)
        return None


async def validate_enrollee_eligibility(cifno: str, provider_id: str) -> dict:
    """
    Validate enrollee eligibility and provider access via the Prognosis API.

    GET /api/ProviderNetwork/ValidateEnrolleeProviderAccessList
        ?cifno={cifno}&providerid={provider_id}
    """
    if not settings.PROGNOSIS_BASE_URL:
        log.warning("PROGNOSIS_BASE_URL not configured — skipping eligibility check")
        return {
            "is_eligible": False,
            "reason": "Prognosis API not configured",
            "prognosis_response": None,
        }

    token = await _get_prognosis_token()
    if not token:
        return {
            "is_eligible": False,
            "reason": "Failed to authenticate with Prognosis API",
            "prognosis_response": None,
        }

    url = (
        f"{settings.PROGNOSIS_BASE_URL}/api/ProviderNetwork"
        f"/ValidateEnrolleeProviderAccessList"
    )
    params = {"cifno": cifno, "providerid": provider_id}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(url, params=params, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            log.info("Prognosis eligibility for cifno=%s providerid=%s: %s", cifno, provider_id, data)
            return {
                "is_eligible": True,
                "reason": None,
                "prognosis_response": data,
            }
        elif resp.status_code == 401:
            # Token expired — clear cache and retry once
            global _prognosis_token_expiry
            _prognosis_token_expiry = 0
            token = await _get_prognosis_token()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
                    resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "is_eligible": True,
                        "reason": None,
                        "prognosis_response": data,
                    }
            return {
                "is_eligible": False,
                "reason": "Prognosis authentication expired",
                "prognosis_response": None,
            }
        else:
            log.warning(
                "Prognosis eligibility returned %d for cifno=%s: %s",
                resp.status_code, cifno, resp.text[:300],
            )
            return {
                "is_eligible": False,
                "reason": f"Prognosis returned status {resp.status_code}",
                "prognosis_response": None,
            }
    except httpx.RequestError as e:
        log.error("Prognosis eligibility request failed: %s", e)
        return {
            "is_eligible": False,
            "reason": f"Cannot reach Prognosis API: {e}",
            "prognosis_response": None,
        }


async def submit_claim_verification(
    verification_token: str, provider_id: str, timestamp: str
) -> dict | None:
    """Notify Prognosis that a verified visit occurred."""
    if not settings.PROGNOSIS_BASE_URL:
        return None

    token = await _get_prognosis_token()
    if not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(
                f"{settings.PROGNOSIS_BASE_URL}/api/claims/verify",
                json={
                    "verification_token": verification_token,
                    "provider_id": provider_id,
                    "timestamp": timestamp,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return resp.json()
            return None
    except httpx.RequestError as e:
        log.error("Prognosis claim verification failed: %s", e)
        return None


async def flag_impersonation(member_id: str, provider_id: str) -> None:
    """Report a biometric mismatch to Prognosis for fraud investigation."""
    if not settings.PROGNOSIS_BASE_URL:
        return

    token = await _get_prognosis_token()
    if not token:
        return

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            await client.post(
                f"{settings.PROGNOSIS_BASE_URL}/api/fraud/flag",
                json={"member_id": member_id, "provider_id": provider_id},
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.RequestError as e:
        log.error("Prognosis fraud flag failed: %s", e)


async def get_claims_by_member(cifno: str) -> dict:
    """
    Get reimbursement claims status for a member by CIF number.

    Calls: GET /api/Claims/GetClaimsByMemberId?cifno={cifno}
    """
    if not settings.PROGNOSIS_BASE_URL:
        return {
            "success": False,
            "reason": "Prognosis API not configured",
            "claims": [],
        }

    token = await _get_prognosis_token()
    if not token:
        return {
            "success": False,
            "reason": "Failed to authenticate with Prognosis API",
            "claims": [],
        }

    url = f"{settings.PROGNOSIS_BASE_URL}/api/Claims/GetClaimsByMemberId"
    params = {"cifno": cifno}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(url, params=params, headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            log.info("Prognosis claims for cifno=%s: %d records", cifno, len(data) if isinstance(data, list) else 1)
            claims = data if isinstance(data, list) else [data] if data else []
            return {
                "success": True,
                "reason": None,
                "claims": claims,
            }
        elif resp.status_code == 401:
            global _prognosis_token_expiry
            _prognosis_token_expiry = 0
            token = await _get_prognosis_token()
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
                    resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    claims = data if isinstance(data, list) else [data] if data else []
                    return {"success": True, "reason": None, "claims": claims}
            return {"success": False, "reason": "Prognosis authentication expired", "claims": []}
        elif resp.status_code == 404:
            return {"success": True, "reason": "No claims found for this member", "claims": []}
        else:
            log.warning("Prognosis claims returned %d for cifno=%s", resp.status_code, cifno)
            return {
                "success": False,
                "reason": f"Prognosis returned status {resp.status_code}",
                "claims": [],
            }
    except httpx.RequestError as e:
        log.error("Prognosis claims request failed: %s", e)
        return {
            "success": False,
            "reason": f"Cannot reach Prognosis API: {e}",
            "claims": [],
        }
