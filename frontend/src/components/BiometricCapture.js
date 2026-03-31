import React, { useState } from "react";
import { captureBiometric } from "../services/api";
import { captureFromDevice } from "../services/fingerprintBridge";
import styles from "./shared.module.css";

export default function BiometricCapture({ member, onComplete }) {
  const [nin, setNin] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanPhase, setScanPhase] = useState("");
  const [error, setError] = useState("");

  const handleCapture = async () => {
    setError("");
    setScanning(true);
    setScanPhase("Place finger on the FS80H scanner...");
    try {
      // Step 1: capture from Futronic FS80H via scanner agent
      const { template, imageQuality, lfdPassed } = await captureFromDevice({
        requireLFD: true,
      });

      setScanPhase("Enrolling biometric...");

      // Step 2: send to backend for enrollment (includes LFD + quality metadata)
      const { data } = await captureBiometric(
        member.member_id,
        template,
        "right_thumb",
        nin || null,
        lfdPassed,
        imageQuality
      );
      onComplete(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Capture failed");
    } finally {
      setScanning(false);
      setScanPhase("");
    }
  };

  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>Biometric Enrollment</h3>
      <p className={styles.cardSubtitle}>
        No biometric on file. Place the member's finger on the Futronic FS80H
        scanner to register.
      </p>

      {error && <div className={styles.error}>{error}</div>}

      <label className={styles.label}>
        NIN (optional)
        <input
          type="text"
          value={nin}
          onChange={(e) => setNin(e.target.value)}
          placeholder="National Identification Number"
          className={styles.input}
        />
      </label>

      {scanPhase && <div className={styles.scanStatus}>{scanPhase}</div>}

      <button
        onClick={handleCapture}
        disabled={scanning}
        className={styles.primaryBtn}
      >
        {scanning ? "Scanning..." : "Capture Fingerprint"}
      </button>
    </div>
  );
}
