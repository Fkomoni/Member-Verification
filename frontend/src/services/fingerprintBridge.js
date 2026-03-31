/**
 * Fingerprint Device Bridge
 *
 * This module abstracts the communication with the physical fingerprint
 * scanner. Replace the implementation inside `captureFromDevice()` with
 * calls to your vendor's JavaScript/WebSocket SDK.
 *
 * Supported integration patterns:
 *
 * 1. **WebSocket SDK** (most common)
 *    - The device vendor runs a local agent/service on the PC.
 *    - The browser connects via WebSocket (e.g., ws://localhost:8089).
 *    - Send a "capture" command; receive the fingerprint template as
 *      a base64 string.
 *
 * 2. **Browser Plugin / ActiveX** (legacy)
 *    - Vendor provides a browser extension exposing a JS API.
 *
 * 3. **Native Messaging / Electron bridge**
 *    - If your portal runs in Electron, you can call the native SDK
 *      directly via Node.js child_process or ffi-napi.
 *
 * Example vendors: SecuGen, DigitalPersona, Futronic, Suprema, ZKTeco.
 */

/**
 * Capture a fingerprint template from the connected scanner device.
 *
 * @returns {Promise<string>} base64-encoded fingerprint template
 */
export async function captureFromDevice() {
  // ─── REPLACE THIS BLOCK WITH YOUR VENDOR SDK ───────────────
  //
  // Example for a WebSocket-based SDK:
  //
  //   const ws = new WebSocket("ws://localhost:8089/fingerprint");
  //   return new Promise((resolve, reject) => {
  //     ws.onopen = () => ws.send(JSON.stringify({ command: "capture" }));
  //     ws.onmessage = (evt) => {
  //       const data = JSON.parse(evt.data);
  //       if (data.status === "ok") {
  //         resolve(data.template);  // base64 string
  //       } else {
  //         reject(new Error(data.error || "Capture failed"));
  //       }
  //       ws.close();
  //     };
  //     ws.onerror = () => reject(new Error("Scanner not connected"));
  //   });
  //
  // ─── DEMO STUB (remove in production) ──────────────────────
  return new Promise((resolve, reject) => {
    // Simulate a 2-second scan delay
    setTimeout(() => {
      // In demo mode, return a dummy template.
      // In production, this comes from the physical device.
      const demoTemplate = btoa(
        "DEMO_FINGERPRINT_TEMPLATE_" + Date.now()
      );
      resolve(demoTemplate);
    }, 2000);
  });
}

/**
 * Check if the fingerprint scanner device is connected and responsive.
 *
 * @returns {Promise<boolean>}
 */
export async function isDeviceConnected() {
  // Replace with actual device health check
  // e.g., ping the WebSocket endpoint
  try {
    await captureFromDevice();
    return true;
  } catch {
    return false;
  }
}
