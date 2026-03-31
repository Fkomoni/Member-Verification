import React, { useState } from "react";
import { validateFingerprint } from "../services/api";
import { captureFromDevice } from "../services/fingerprintBridge";
import styles from "./shared.module.css";

export default function FingerprintValidation({ member, onResult }) {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  const handleValidate = async () => {
    setError("");
    setScanning(true);
    try {
      const templateB64 = await captureFromDevice();
      const { data } = await validateFingerprint(member.member_id, templateB64);
      onResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Validation failed");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>Fingerprint Verification</h3>
      <p className={styles.cardSubtitle}>
        Place the member's finger on the scanner to verify identity.
      </p>

      {error && <div className={styles.error}>{error}</div>}

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
