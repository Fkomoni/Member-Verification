import React from "react";
import styles from "./shared.module.css";

export default function MemberCard({ member }) {
  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>{member.name}</h3>
      <div className={styles.detailGrid}>
        <Detail label="Enrollee ID" value={member.enrollee_id} />
        <Detail label="Gender" value={member.gender || "N/A"} />
        <Detail label="DOB" value={member.dob ? new Date(member.dob).toLocaleDateString() : "N/A"} />
        <Detail label="NIN" value={member.nin || "Not captured"} />
        <Detail
          label="Biometric"
          value={member.biometric_registered ? "Registered" : "Not registered"}
          highlight={!member.biometric_registered}
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
