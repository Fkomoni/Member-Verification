import React, { useState } from "react";
import { validateFingerprint } from "../services/api";
import { captureFromDevice } from "../services/fingerprintBridge";
import styles from "./shared.module.css";

export default function FingerprintValidation({ member, onResult }) {
  const [scanning, setScanning] = useState(false);
  const [scanPhase, setScanPhase] = useState("");
  const [error, setError] = useState("");

  const handleValidate = async () => {
    setError("");
    setScanning(true);
    setScanPhase("Place finger on the FS80H scanner...");
    try {
      // Capture from Futronic FS80H with LFD enforced
      const { template, imageQuality, lfdPassed } = await captureFromDevice({
        requireLFD: true,
      });

      setScanPhase("Verifying identity...");

      // Send to backend (includes LFD + quality metadata)
      const { data } = await validateFingerprint(
        member.member_id,
        template,
        lfdPassed,
        imageQuality
      );
      onResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Validation failed");
    } finally {
      setScanning(false);
      setScanPhase("");
    }
  };

  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>Fingerprint Verification</h3>
      <p className={styles.cardSubtitle}>
        Place the member's finger on the FS80H scanner to verify identity.
        Live Finger Detection is active.
      </p>

      {error && <div className={styles.error}>{error}</div>}

      {scanPhase && <div className={styles.scanStatus}>{scanPhase}</div>}

      <button
        onClick={handleValidate}
        disabled={scanning}
        className={styles.primaryBtn}
      >
        {scanning ? "Scanning..." : "Scan Fingerprint"}
      </button>
    </div>
  );
}
