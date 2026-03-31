import React from "react";
import styles from "./shared.module.css";

export default function VerificationResult({ result, onReset }) {
  const statusClass =
    result.status === "approved" || result.status === "enrolled"
      ? styles.successBanner
      : styles.errorBanner;

  const statusLabel = {
    approved: "APPROVED",
    enrolled: "ENROLLED",
    denied: "DENIED",
  }[result.status];

  return (
    <div className={styles.card}>
      <div className={statusClass}>
        <span className={styles.statusLabel}>{statusLabel}</span>
      </div>
      <p className={styles.resultMessage}>{result.message}</p>

      {result.verificationToken && (
        <div className={styles.tokenBox}>
          <span className={styles.detailLabel}>Verification Token</span>
          <code className={styles.tokenCode}>
            {result.verificationToken.slice(0, 40)}...
          </code>
        </div>
      )}

      <button onClick={onReset} className={styles.secondaryBtn}>
        Verify Another Member
      </button>
    </div>
  );
}
