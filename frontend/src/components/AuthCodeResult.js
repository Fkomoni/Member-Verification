import React, { useState } from "react";
import styles from "./callcenter.module.css";

export default function AuthCodeResult({ codeData, onDismiss }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeData.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for non-HTTPS
      const textarea = document.createElement("textarea");
      textarea.value = codeData.code;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatAmount = (amount) =>
    new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
    }).format(amount);

  const formatDate = (dateStr) =>
    new Date(dateStr).toLocaleString("en-NG", {
      dateStyle: "medium",
      timeStyle: "short",
    });

  return (
    <div className={styles.resultCard}>
      <div className={styles.resultHeader}>
        <div className={styles.successIcon}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0A7C3E" strokeWidth="2.5">
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        </div>
        <h3 className={styles.resultTitle}>Code Generated Successfully</h3>
      </div>

      <div className={styles.codeDisplay}>
        <span className={styles.codeLabel}>AUTHORIZATION CODE</span>
        <div className={styles.codeValue}>{codeData.code}</div>
        <button
          onClick={handleCopy}
          className={`${styles.copyBtn} ${copied ? styles.copyBtnCopied : ""}`}
        >
          {copied ? (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
              </svg>
              Copy Code
            </>
          )}
        </button>
      </div>

      <div className={styles.resultDetails}>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Member</span>
          <span className={styles.detailValue}>
            {codeData.member_name || codeData.enrollee_id}
          </span>
        </div>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Enrollee ID</span>
          <span className={styles.detailValue}>{codeData.enrollee_id}</span>
        </div>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Approved Amount</span>
          <span className={styles.detailValueHighlight}>
            {formatAmount(codeData.approved_amount)}
          </span>
        </div>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Visit Type</span>
          <span className={styles.detailValue}>{codeData.visit_type}</span>
        </div>
        <div className={styles.detailRow}>
          <span className={styles.detailLabel}>Expires</span>
          <span className={styles.detailValue}>{formatDate(codeData.expires_at)}</span>
        </div>
        {codeData.notes && (
          <div className={`${styles.detailRow} ${styles.detailRowFull}`}>
            <span className={styles.detailLabel}>Notes</span>
            <span className={styles.detailValue}>{codeData.notes}</span>
          </div>
        )}
      </div>

      <button onClick={onDismiss} className={styles.dismissBtn}>
        Generate Another Code
      </button>
    </div>
  );
}
