import React, { useState } from "react";
import { verifyMember } from "../services/api";
import styles from "./shared.module.css";

export default function MemberSearch({ onFound }) {
  const [enrolleeId, setEnrolleeId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await verifyMember(enrolleeId.trim());
      onFound(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Member not found");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Member Verification</h2>
      <p className={styles.cardSubtitle}>
        Enter the enrollee CIF number to check eligibility and begin verification.
      </p>

      {error && <div className={styles.error}>{error}</div>}

      <form onSubmit={handleSearch} className={styles.row}>
        <input
          type="text"
          placeholder="Enrollee CIF Number (e.g. 1738)"
          value={enrolleeId}
          onChange={(e) => setEnrolleeId(e.target.value)}
          required
          className={styles.input}
        />
        <button type="submit" disabled={loading} className={styles.primaryBtn}>
          {loading ? "Checking..." : "Verify Member"}
        </button>
      </form>
    </div>
  );
}
