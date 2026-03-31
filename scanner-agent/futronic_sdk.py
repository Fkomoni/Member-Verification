"""
Futronic FS80H SDK Wrapper (ctypes bindings)

This module wraps the Futronic ftrScanAPI.dll and ftrAnakeySDK.dll via ctypes.
These DLLs ship with the Futronic SDK installer.

PREREQUISITES:
  1. Install the Futronic SDK from the CD/download provided with your FS80H
  2. Install the FS80H USB driver (included in the SDK installer)
  3. Ensure ftrScanAPI.dll and ftrAnakeySDK.dll are on the system PATH,
     or place them in this directory alongside this script.

SDK Download: Contact Futronic (https://www.futronic-tech.com) or use the
CD shipped with the FS80H device.
"""

import ctypes
import ctypes.wintypes
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

# ── Locate DLLs ──────────────────────────────────────────────────────
# The SDK installer typically places these in C:\\Program Files\\Futronic\\SDK\\
# or the user can copy them next to this script.
_SCRIPT_DIR = Path(__file__).parent
_SDK_SEARCH_PATHS = [
    _SCRIPT_DIR,
    Path(r"C:\Program Files\Futronic\SDK\Bin"),
    Path(r"C:\Program Files (x86)\Futronic\SDK\Bin"),
]

_scan_api = None
_anakey_sdk = None


class FutronicError(Exception):
    """Raised when a Futronic SDK call fails."""
    pass


# ── ftrScanAPI Constants ─────────────────────────────────────────────
class FTR_SCAN(IntEnum):
    """ftrScanAPI return codes and constants."""
    OK = 0
    ERROR_EMPTY_FRAME = 4003
    ERROR_MOVABLE_FINGER = 4004
    ERROR_NO_FRAME = 4005
    ERROR_FAKE_FINGER = 4100  # LFD rejection


@dataclass
class FingerprintImage:
    """Raw fingerprint image from the scanner."""
    width: int
    height: int
    data: bytes       # grayscale 8-bit pixel data
    quality: int      # NFIQ-like quality score (0-100)
    lfd_passed: bool


@dataclass
class FingerprintTemplate:
    """Extracted minutiae template."""
    data: bytes       # ANSI 378 encoded template
    quality: int


def _find_dll(name: str) -> str:
    """Search known paths for a Futronic DLL."""
    for search_dir in _SDK_SEARCH_PATHS:
        candidate = search_dir / name
        if candidate.exists():
            return str(candidate)
    # Fall back to system PATH
    return name


def initialize():
    """
    Load Futronic DLLs and initialize the SDK.
    Call once at agent startup.
    """
    global _scan_api, _anakey_sdk

    if sys.platform != "win32":
        raise FutronicError(
            "Futronic SDK requires Windows. On Linux, use the Futronic Linux SDK "
            "(libftrScanAPI.so) — update the ctypes.cdll.LoadLibrary calls accordingly."
        )

    try:
        scan_path = _find_dll("ftrScanAPI.dll")
        _scan_api = ctypes.windll.LoadLibrary(scan_path)
    except OSError as e:
        raise FutronicError(
            f"Cannot load ftrScanAPI.dll: {e}\n"
            "Install the Futronic SDK and ensure ftrScanAPI.dll is accessible."
        ) from e

    try:
        anakey_path = _find_dll("ftrAnakeySDK.dll")
        _anakey_sdk = ctypes.windll.LoadLibrary(anakey_path)
    except OSError as e:
        raise FutronicError(
            f"Cannot load ftrAnakeySDK.dll: {e}\n"
            "Install the Futronic SDK and ensure ftrAnakeySDK.dll is accessible."
        ) from e


def open_device() -> ctypes.c_void_p:
    """
    Open the FS80H scanner device.
    Returns an opaque device handle.
    """
    if _scan_api is None:
        raise FutronicError("SDK not initialized. Call initialize() first.")

    # ftrScanOpenDevice() -> FTRHANDLE
    _scan_api.ftrScanOpenDevice.restype = ctypes.c_void_p
    handle = _scan_api.ftrScanOpenDevice()
    if not handle:
        raise FutronicError(
            "Failed to open FS80H device. Check USB connection and driver."
        )
    return handle


def close_device(handle: ctypes.c_void_p):
    """Close the scanner device."""
    if _scan_api and handle:
        _scan_api.ftrScanCloseDevice(handle)


def set_lfd_enabled(handle: ctypes.c_void_p, enabled: bool):
    """
    Enable or disable the FS80H's hardware Live Finger Detection.
    LFD uses a separate electronic circuit to reject fake fingers
    made from silicone, rubber, play-doh, etc.
    """
    if _scan_api is None:
        raise FutronicError("SDK not initialized.")

    # ftrScanSetOptions(handle, FTR_OPTIONS_CHECK_FAKE_REPLICA, enabled)
    FTR_OPTIONS_CHECK_FAKE_REPLICA = 0x00000020
    value = ctypes.c_ulong(1 if enabled else 0)
    result = _scan_api.ftrScanSetOptions(
        handle,
        ctypes.c_ulong(FTR_OPTIONS_CHECK_FAKE_REPLICA),
        ctypes.byref(value),
    )
    if result != 0:
        raise FutronicError(f"Failed to set LFD option: error code {result}")


def capture_image(handle: ctypes.c_void_p, lfd_enabled: bool = True) -> FingerprintImage:
    """
    Capture a fingerprint image from the FS80H.

    The scanner uses IR illumination with automatic intensity adjustment
    to handle wet, dry, or blurred fingerprints.

    Args:
        handle: Device handle from open_device()
        lfd_enabled: Whether to enforce Live Finger Detection

    Returns:
        FingerprintImage with raw pixel data

    Raises:
        FutronicError if capture fails or LFD rejects the finger
    """
    if _scan_api is None:
        raise FutronicError("SDK not initialized.")

    set_lfd_enabled(handle, lfd_enabled)

    # Get image dimensions
    class FTRSCAN_IMAGE_SIZE(ctypes.Structure):
        _fields_ = [("nWidth", ctypes.c_int), ("nHeight", ctypes.c_int), ("nImageSize", ctypes.c_int)]

    img_size = FTRSCAN_IMAGE_SIZE()
    result = _scan_api.ftrScanGetImageSize(handle, ctypes.byref(img_size))
    if result != 0:
        raise FutronicError(f"Failed to get image size: error code {result}")

    # Allocate buffer and capture
    buffer = (ctypes.c_ubyte * img_size.nImageSize)()
    result = _scan_api.ftrScanGetFrame(handle, buffer, None)

    if result != FTR_SCAN.OK:
        if result == FTR_SCAN.ERROR_FAKE_FINGER:
            raise FutronicError("LFD_REJECTED: Fake finger detected by FS80H hardware")
        if result == FTR_SCAN.ERROR_EMPTY_FRAME:
            raise FutronicError("No finger detected on scanner")
        if result == FTR_SCAN.ERROR_MOVABLE_FINGER:
            raise FutronicError("Finger moved during scan. Hold still and try again.")
        raise FutronicError(f"Capture failed: error code {result}")

    # Check LFD result
    lfd_passed = True
    if lfd_enabled:
        is_fake = ctypes.c_bool(False)
        _scan_api.ftrScanIsFakeReplica(handle, buffer, ctypes.byref(is_fake))
        if is_fake.value:
            raise FutronicError("LFD_REJECTED: Fake finger detected by FS80H hardware")

    return FingerprintImage(
        width=img_size.nWidth,
        height=img_size.nHeight,
        data=bytes(buffer),
        quality=_compute_image_quality(bytes(buffer), img_size.nWidth, img_size.nHeight),
        lfd_passed=lfd_passed,
    )


def extract_template(image: FingerprintImage) -> FingerprintTemplate:
    """
    Extract an ANSI 378 minutiae template from a fingerprint image
    using ftrAnakeySDK.

    The template contains only minutiae points (ridge endings and
    bifurcations) — not the raw image. This is what gets encrypted
    and stored in the database.
    """
    if _anakey_sdk is None:
        raise FutronicError("ftrAnakeySDK not initialized.")

    # Allocate template buffer (max 2KB for ANSI 378)
    MAX_TEMPLATE_SIZE = 2048
    template_buf = (ctypes.c_ubyte * MAX_TEMPLATE_SIZE)()
    template_size = ctypes.c_int(MAX_TEMPLATE_SIZE)

    result = _anakey_sdk.AnakeyExtract(
        ctypes.c_void_p(None),  # use default context
        image.data,
        ctypes.c_int(image.width),
        ctypes.c_int(image.height),
        template_buf,
        ctypes.byref(template_size),
    )
    if result != 0:
        raise FutronicError(f"Template extraction failed: error code {result}")

    return FingerprintTemplate(
        data=bytes(template_buf[: template_size.value]),
        quality=image.quality,
    )


def match_templates(template1: bytes, template2: bytes, threshold: int = 800) -> tuple[bool, int]:
    """
    Compare two ANSI 378 minutiae templates using ftrAnakeySDK.

    Args:
        template1: First template (e.g., live scan)
        template2: Second template (e.g., stored enrollment)
        threshold: Match score threshold (default 800, range 0-10000).
                   Higher = stricter. Recommended: 800 for 1:1 verification.

    Returns:
        (matched: bool, score: int)
    """
    if _anakey_sdk is None:
        raise FutronicError("ftrAnakeySDK not initialized.")

    score = ctypes.c_int(0)
    result = _anakey_sdk.AnakeyVerify(
        ctypes.c_void_p(None),  # default context
        template1,
        ctypes.c_int(len(template1)),
        template2,
        ctypes.c_int(len(template2)),
        ctypes.byref(score),
    )
    if result != 0:
        raise FutronicError(f"Template matching failed: error code {result}")

    return (score.value >= threshold, score.value)


def _compute_image_quality(data: bytes, width: int, height: int) -> int:
    """
    Compute a simple image quality score (0-100) based on pixel contrast.
    In production, use NIST NFIQ or the SDK's built-in quality assessment.
    """
    if not data:
        return 0
    pixel_values = list(data)
    mean = sum(pixel_values) / len(pixel_values)
    variance = sum((p - mean) ** 2 for p in pixel_values) / len(pixel_values)
    # Map variance to 0-100 score (higher variance = better contrast)
    score = min(100, int((variance / 2000) * 100))
    return max(0, score)
