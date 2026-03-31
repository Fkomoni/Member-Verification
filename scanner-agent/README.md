# Futronic FS80H Scanner Agent

Local WebSocket service that runs on each provider workstation and bridges
the Futronic FS80H USB fingerprint scanner to the browser-based portal.

## Architecture

```
Browser (React)  ←── WebSocket ──→  Scanner Agent (Python)  ←── USB ──→  FS80H
    :3000                               :8089                            Hardware
```

## Prerequisites

1. **Futronic FS80H** connected via USB
2. **Futronic SDK** installed (provides `ftrScanAPI.dll` and `ftrAnakeySDK.dll`)
   - Download from [Futronic](https://www.futronic-tech.com) or use the CD shipped with the device
   - Run the SDK installer — it installs drivers and DLLs
3. **Python 3.10+** on the workstation

## Installation

```bash
cd scanner-agent
pip install -r requirements.txt
```

Ensure the Futronic DLLs are accessible:
- Option A: They're on the system PATH (SDK installer does this)
- Option B: Copy `ftrScanAPI.dll` and `ftrAnakeySDK.dll` into this directory

## Running

```bash
python agent.py --port 8089
```

The agent will:
1. Load the Futronic SDK DLLs
2. Open the FS80H device
3. Start a WebSocket server on `ws://localhost:8089`
4. Wait for commands from the browser

## Commands

### `capture`
Scan a fingerprint and return the minutiae template.

```json
{ "command": "capture", "params": { "lfd_enabled": true } }
```

Response:
```json
{
  "status": "ok",
  "template": "<base64-encoded ANSI 378 template>",
  "quality": 85,
  "lfd_passed": true
}
```

If LFD rejects a fake finger:
```json
{
  "status": "lfd_failed",
  "message": "Live Finger Detection failed — fake finger detected"
}
```

### `status`
Check if the scanner is connected.

```json
{ "command": "status" }
```

Response:
```json
{
  "status": "ok",
  "device_connected": true,
  "device_model": "Futronic FS80H",
  "lfd_supported": true
}
```

## FS80H Features Used

| Feature | Purpose |
|---------|---------|
| CMOS sensor + precise optics | High-quality undistorted fingerprint images |
| IR LED illumination | Handles wet, dry, and blurred fingerprints |
| Auto intensity adjustment | Optimizes image quality per finger |
| Live Finger Detection (LFD) | Hardware circuit rejects silicone/rubber/play-doh fakes |
| USB 2.0 | Fast image transfer |

## Deploying to Workstations

For production rollout:

1. Create a Windows installer (e.g., with PyInstaller or NSIS) that bundles:
   - Python runtime
   - This agent script
   - Futronic SDK DLLs
2. Install as a Windows Service (use `nssm` or `pywin32`) so it auto-starts
3. Configure the React app's `REACT_APP_SCANNER_AGENT_URL` to point to `ws://localhost:8089`
