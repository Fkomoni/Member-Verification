import React from "react";
import styles from "./shared.module.css";

const STATUS_CONFIG = {
  eligible: {
    bannerClass: styles.eligibleBanner,
    label: "ELIGIBLE",
  },
  enrolled: {
    bannerClass: styles.enrolledBanner,
    label: "ENROLLED",
  },
  unverified: {
    bannerClass: styles.unverifiedBanner,
    label: "UNVERIFIED",
  },
  denied: {
    bannerClass: styles.deniedBanner,
    label: "DENIED",
  },
  ineligible: {
    bannerClass: styles.ineligibleBanner,
    label: "INELIGIBLE",
  },
};

export default function VerificationResult({ result, onReset }) {
  const config = STATUS_CONFIG[result.status] || STATUS_CONFIG.denied;

  return (
    <div className={styles.card}>
      <div className={config.bannerClass}>
        <span className={styles.statusLabel}>{config.label}</span>
      </div>

      <p className={styles.resultMessage}>{result.message}</p>

      {result.verificationReason && (
        <p className={styles.resultReason}>{result.verificationReason}</p>
      )}

      {result.verificationToken && (
        <div className={styles.tokenBox}>
          <span className={styles.detailLabel}>Verification Token</span>
          <code className={styles.tokenCode}>
            {result.verificationToken.slice(0, 50)}...
          </code>
        </div>
      )}

      <button onClick={onReset} className={styles.secondaryBtn}>
        Verify Another Member
      </button>
    </div>
  );
}
