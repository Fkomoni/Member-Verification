"""
Futronic FS80H Scanner Agent — WebSocket Service

This lightweight service runs on each provider workstation alongside the
browser. It bridges the Futronic native SDK (USB) to a WebSocket that the
React portal connects to.

Usage:
    python agent.py [--port 8089]

The browser sends JSON commands:
    { "command": "capture", "params": { "lfd_enabled": true } }
    { "command": "status" }

The agent responds with JSON:
    { "status": "ok", "template": "<base64>", "quality": 85, "lfd_passed": true }
    { "status": "error", "message": "..." }
    { "status": "lfd_failed", "message": "Fake finger detected" }
"""

import argparse
import asyncio
import base64
import json
import logging
import signal
import sys

import websockets

import futronic_sdk as ftr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("futronic-agent")

# Global device handle (single scanner per workstation)
_device_handle = None


def init_scanner():
    """Initialize SDK and open the FS80H device."""
    global _device_handle
    log.info("Initializing Futronic SDK...")
    ftr.initialize()
    log.info("Opening FS80H device...")
    _device_handle = ftr.open_device()
    log.info("FS80H scanner ready.")


def shutdown_scanner():
    """Clean up device handle."""
    global _device_handle
    if _device_handle:
        log.info("Closing FS80H device...")
        ftr.close_device(_device_handle)
        _device_handle = None


async def handle_capture(params: dict) -> dict:
    """Handle a fingerprint capture request."""
    lfd_enabled = params.get("lfd_enabled", True)

    try:
        # Capture image from FS80H
        image = ftr.capture_image(_device_handle, lfd_enabled=lfd_enabled)

        # Extract minutiae template
        template = ftr.extract_template(image)

        # Encode template as base64 for transport
        template_b64 = base64.b64encode(template.data).decode("ascii")

        return {
            "status": "ok",
            "template": template_b64,
            "quality": template.quality,
            "lfd_passed": image.lfd_passed,
        }

    except ftr.FutronicError as e:
        error_msg = str(e)
        if "LFD_REJECTED" in error_msg:
            log.warning("LFD rejected: fake finger detected")
            return {
                "status": "lfd_failed",
                "message": "Live Finger Detection failed — fake finger detected",
            }
        log.error("Capture error: %s", error_msg)
        return {"status": "error", "message": error_msg}


async def handle_status() -> dict:
    """Return device status information."""
    connected = _device_handle is not None
    return {
        "status": "ok",
        "device_connected": connected,
        "device_model": "Futronic FS80H",
        "lfd_supported": True,
        "serial_number": None,  # populated if SDK exposes serial
        "firmware_version": None,
    }


async def handle_connection(websocket):
    """Handle a single WebSocket connection from the browser."""
    remote = websocket.remote_address
    log.info("Client connected: %s", remote)

    try:
        async for raw_message in websocket:
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send(
                    json.dumps({"status": "error", "message": "Invalid JSON"})
                )
                continue

            command = message.get("command")
            params = message.get("params", {})
            log.info("Command: %s from %s", command, remote)

            if command == "capture":
                # Notify client we're waiting for finger placement
                await websocket.send(
                    json.dumps({"status": "waiting", "message": "Place finger on scanner"})
                )
                result = await handle_capture(params)
                await websocket.send(json.dumps(result))

            elif command == "status":
                result = await handle_status()
                await websocket.send(json.dumps(result))

            else:
                await websocket.send(
                    json.dumps({"status": "error", "message": f"Unknown command: {command}"})
                )

    except websockets.ConnectionClosed:
        log.info("Client disconnected: %s", remote)


async def main(port: int):
    """Start the WebSocket server."""
    init_scanner()

    log.info("Starting Futronic Scanner Agent on ws://localhost:%d", port)

    stop = asyncio.Event()

    def signal_handler():
        stop.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: signal_handler())

    async with websockets.serve(
        handle_connection,
        "localhost",
        port,
        origins=["http://localhost:3000", "https://portal.yourdomain.com"],
    ):
        log.info("Scanner Agent ready. Waiting for connections...")
        await stop.wait()

    shutdown_scanner()
    log.info("Scanner Agent shut down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Futronic FS80H Scanner Agent")
    parser.add_argument("--port", type=int, default=8089, help="WebSocket port (default: 8089)")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        pass
