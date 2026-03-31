import React, { useState } from "react";
import { captureBiometric } from "../services/api";
import { captureFromDevice } from "../services/fingerprintBridge";
import styles from "./shared.module.css";

export default function BiometricCapture({ member, onComplete }) {
  const [nin, setNin] = useState("");
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  const handleCapture = async () => {
    setError("");
    setScanning(true);
    try {
      // Step 1: capture from fingerprint device
      const templateB64 = await captureFromDevice();

      // Step 2: send to backend for enrollment
      const { data } = await captureBiometric(
        member.member_id,
        templateB64,
        "right_thumb",
        nin || null
      );
      onComplete(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Capture failed");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>Biometric Enrollment</h3>
      <p className={styles.cardSubtitle}>
        No biometric on file. Capture fingerprint to register this member.
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

      <button
        onClick={handleCapture}
        disabled={scanning}
        className={styles.primaryBtn}
      >
        {scanning ? "Scanning fingerprint..." : "Capture Fingerprint"}
      </button>
    </div>
  );
}
