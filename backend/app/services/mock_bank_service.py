"""
Mock Bank Validation Service — validates bank account details.

PLACEHOLDER: Replace with real bank verification API (e.g. Paystack, Flutterwave)
when available. Currently returns mock account names for known test accounts.
"""

import logging

log = logging.getLogger(__name__)

# Nigerian bank list (common banks)
NIGERIAN_BANKS = [
    "Access Bank",
    "Citibank Nigeria",
    "Ecobank Nigeria",
    "Fidelity Bank",
    "First Bank of Nigeria",
    "First City Monument Bank (FCMB)",
    "Globus Bank",
    "Guaranty Trust Bank (GTBank)",
    "Heritage Bank",
    "Jaiz Bank",
    "Keystone Bank",
    "Kuda Bank",
    "Opay",
    "Palmpay",
    "Parallex Bank",
    "Polaris Bank",
    "Providus Bank",
    "Stanbic IBTC Bank",
    "Standard Chartered Bank",
    "Sterling Bank",
    "SunTrust Bank",
    "Titan Trust Bank",
    "Union Bank of Nigeria",
    "United Bank for Africa (UBA)",
    "Unity Bank",
    "VFD Microfinance Bank",
    "Wema Bank",
    "Zenith Bank",
]

# Mock account data for testing
_MOCK_ACCOUNTS = {
    ("Zenith Bank", "2012345678"): "Adebayo Ogunlesi",
    ("GTBank", "0123456789"): "Chioma Eze",
    ("Guaranty Trust Bank (GTBank)", "0123456789"): "Chioma Eze",
    ("First Bank of Nigeria", "3012345678"): "Fatima Abdullahi",
    ("Access Bank", "0012345678"): "Emeka Okoro",
    ("United Bank for Africa (UBA)", "1012345678"): "Funke Adeyemi",
}


def get_bank_list() -> list[str]:
    """Return list of supported Nigerian banks."""
    return NIGERIAN_BANKS


def validate_bank_account(
    bank_name: str, account_number: str
) -> dict:
    """
    Validate a bank account and return the account holder name.

    PLACEHOLDER: Currently uses mock data. Replace with real bank
    verification API (Paystack Resolve Account, Flutterwave, etc.)

    Returns: { valid: bool, account_name: str | None, message: str }
    """
    # Basic validation
    if not account_number or len(account_number) != 10:
        return {
            "valid": False,
            "account_name": None,
            "message": "Account number must be 10 digits",
        }

    if bank_name not in NIGERIAN_BANKS:
        return {
            "valid": False,
            "account_name": None,
            "message": f"Bank '{bank_name}' is not recognized",
        }

    # Check mock data
    account_name = _MOCK_ACCOUNTS.get((bank_name, account_number))
    if account_name:
        log.info("Bank validation (mock): %s/%s → %s", bank_name, account_number, account_name)
        return {
            "valid": True,
            "account_name": account_name,
            "message": "Account validated successfully",
        }

    # PLACEHOLDER: For unknown accounts, generate a plausible response
    # In production, this would call the bank verification API
    log.info(
        "Bank validation (mock fallback): %s/%s — returning placeholder name",
        bank_name,
        account_number,
    )
    return {
        "valid": True,
        "account_name": "ACCOUNT HOLDER (Pending Verification)",
        "message": "Account accepted — name will be verified via bank API",
    }
