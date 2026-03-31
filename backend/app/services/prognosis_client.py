"""
Client for integrating with the Prognosis core HMO system.

All outbound calls to Prognosis go through this module so they can be
mocked in tests and swapped for real endpoints when ready.
"""

import httpx

from backend.app.core.config import settings

_TIMEOUT = httpx.Timeout(30.0)


async def lookup_member(enrollee_id: str) -> dict | None:
    """
    Look up a member in the Prognosis system by enrollee ID.
    Returns member data dict or None if not found.
    """
    if not settings.PROGNOSIS_BASE_URL or not settings.PROGNOSIS_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{settings.PROGNOSIS_BASE_URL}/members/{enrollee_id}",
            headers={"Authorization": f"Bearer {settings.PROGNOSIS_API_KEY}"},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


async def submit_claim_verification(
    verification_token: str, provider_id: str, timestamp: str
) -> dict | None:
    """
    Notify Prognosis that a verified visit occurred, enabling claims processing.
    """
    if not settings.PROGNOSIS_BASE_URL or not settings.PROGNOSIS_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.PROGNOSIS_BASE_URL}/claims/verify",
            json={
                "verification_token": verification_token,
                "provider_id": provider_id,
                "timestamp": timestamp,
            },
            headers={"Authorization": f"Bearer {settings.PROGNOSIS_API_KEY}"},
        )
        if resp.status_code == 200:
            return resp.json()
        return None


async def flag_impersonation(member_id: str, provider_id: str) -> None:
    """
    Report a biometric mismatch to Prognosis for fraud investigation.
    """
    if not settings.PROGNOSIS_BASE_URL or not settings.PROGNOSIS_API_KEY:
        return

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        await client.post(
            f"{settings.PROGNOSIS_BASE_URL}/fraud/flag",
            json={"member_id": member_id, "provider_id": provider_id},
            headers={"Authorization": f"Bearer {settings.PROGNOSIS_API_KEY}"},
        )
