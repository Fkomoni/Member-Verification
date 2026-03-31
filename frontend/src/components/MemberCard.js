import React from "react";
import styles from "./shared.module.css";

export default function MemberCard({ member }) {
  const statusMap = {
    ELIGIBLE: { label: "ELIGIBLE", className: styles.badgeEligible },
    UNVERIFIED: { label: "UNVERIFIED", className: styles.badgeUnverified },
    INELIGIBLE: { label: "INELIGIBLE", className: styles.badgeIneligible },
  };

  const badge = statusMap[member.verification_status] || statusMap.UNVERIFIED;

  return (
    <div className={styles.card}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
        <h3 className={styles.cardTitle}>{member.name}</h3>
        <span className={`${styles.statusBadge} ${badge.className}`}>
          {badge.label}
        </span>
      </div>

      {member.verification_reason && (
        <p className={styles.resultReason}>{member.verification_reason}</p>
      )}

      <div className={styles.detailGrid}>
        <Detail label="Enrollee ID" value={member.enrollee_id} />
        <Detail label="Gender" value={member.gender || "N/A"} />
        <Detail
          label="Date of Birth"
          value={member.dob ? new Date(member.dob).toLocaleDateString() : "N/A"}
        />
        <Detail label="NIN" value={member.nin || "Not captured"} />
        <Detail
          label="Biometric"
          value={member.biometric_registered ? "Registered" : "Not registered"}
          highlight={!member.biometric_registered}
        />
        <Detail
          label="Prognosis"
          value={member.prognosis_eligible ? "Eligible" : "Not eligible"}
          highlight={!member.prognosis_eligible}
        />
      </div>
    </div>
  );
}

function Detail({ label, value, highlight }) {
  return (
    <div>
      <span className={styles.detailLabel}>{label}</span>
      <span className={highlight ? styles.detailValueWarn : styles.detailValue}>
        {value}
      </span>
    </div>
  );
}
