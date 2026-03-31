/**
 * Futronic FS80H Fingerprint Scanner Bridge
 *
 * Communicates with the Futronic Scanner Agent (a local Python/WebSocket
 * service running on the provider's workstation) that wraps ftrScanAPI.
 *
 * Architecture:
 *   Browser  <──WebSocket──>  Scanner Agent (localhost:8089)  <──USB──>  FS80H
 *
 * The scanner agent handles:
 *   - Device open/close via ftrScanAPI
 *   - Image capture with IR illumination auto-adjust
 *   - Live Finger Detection (LFD) hardware check
 *   - Minutiae template extraction via ftrAnakeySDK
 *   - Returns base64-encoded template to the browser
 */

const AGENT_URL =
  process.env.REACT_APP_SCANNER_AGENT_URL || "ws://localhost:8089";

const CAPTURE_TIMEOUT_MS = 30000; // 30s max wait for finger placement

/**
 * Capture a fingerprint template from the Futronic FS80H.
 *
 * @param {object} options
 * @param {boolean} options.requireLFD  Enforce Live Finger Detection (default true)
 * @param {number}  options.timeout     Timeout in ms (default 30000)
 * @returns {Promise<{ template: string, imageQuality: number, lfdPassed: boolean }>}
 */
export async function captureFromDevice({
  requireLFD = true,
  timeout = CAPTURE_TIMEOUT_MS,
} = {}) {
  return new Promise((resolve, reject) => {
    let ws;
    let timer;

    try {
      ws = new WebSocket(AGENT_URL);
    } catch (err) {
      reject(new Error("Cannot connect to fingerprint scanner agent. Is the Futronic Scanner Agent running?"));
      return;
    }

    timer = setTimeout(() => {
      ws.close();
      reject(new Error("Fingerprint capture timed out. Ensure finger is placed on the FS80H scanner."));
    }, timeout);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          command: "capture",
          params: {
            lfd_enabled: requireLFD,
            image_format: "ANSI_378",  // ANSI/INCITS 378 minutiae template
          },
        })
      );
    };

    ws.onmessage = (evt) => {
      clearTimeout(timer);
      try {
        const data = JSON.parse(evt.data);

        if (data.status === "error") {
          reject(new Error(data.message || "Scanner capture failed"));
          ws.close();
          return;
        }

        if (data.status === "lfd_failed") {
          reject(
            new Error("Live Finger Detection failed — fake finger detected. Use a real finger.")
          );
          ws.close();
          return;
        }

        if (data.status === "ok") {
          resolve({
            template: data.template,       // base64-encoded minutiae template
            imageQuality: data.quality,     // 0-100 NFIQ score
            lfdPassed: data.lfd_passed,
          });
          ws.close();
          return;
        }

        // Intermediate status (e.g., "waiting_for_finger") — keep connection open
        if (data.status === "waiting") {
          // Optionally dispatch a UI event for "place finger" feedback
          return;
        }
      } catch (parseErr) {
        reject(new Error("Invalid response from scanner agent"));
        ws.close();
      }
    };

    ws.onerror = () => {
      clearTimeout(timer);
      reject(
        new Error(
          "Fingerprint scanner not connected. Please ensure:\n" +
          "1. The Futronic FS80H is plugged in via USB\n" +
          "2. The Scanner Agent service is running (futronic_agent.py)"
        )
      );
    };

    ws.onclose = (evt) => {
      clearTimeout(timer);
      if (!evt.wasClean && evt.code !== 1000) {
        reject(new Error("Scanner connection closed unexpectedly"));
      }
    };
  });
}

/**
 * Check if the FS80H scanner and agent are reachable.
 *
 * @returns {Promise<{ connected: boolean, deviceInfo: object|null }>}
 */
export async function getDeviceStatus() {
  return new Promise((resolve) => {
    let ws;
    try {
      ws = new WebSocket(AGENT_URL);
    } catch {
      resolve({ connected: false, deviceInfo: null });
      return;
    }

    const timer = setTimeout(() => {
      ws.close();
      resolve({ connected: false, deviceInfo: null });
    }, 3000);

    ws.onopen = () => {
      ws.send(JSON.stringify({ command: "status" }));
    };

    ws.onmessage = (evt) => {
      clearTimeout(timer);
      try {
        const data = JSON.parse(evt.data);
        resolve({
          connected: data.device_connected === true,
          deviceInfo: {
            model: data.device_model || "Futronic FS80H",
            serial: data.serial_number || null,
            lfdSupported: data.lfd_supported === true,
            firmwareVersion: data.firmware_version || null,
          },
        });
      } catch {
        resolve({ connected: false, deviceInfo: null });
      }
      ws.close();
    };

    ws.onerror = () => {
      clearTimeout(timer);
      resolve({ connected: false, deviceInfo: null });
    };
  });
}
