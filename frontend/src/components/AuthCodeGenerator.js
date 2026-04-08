import React, { useState } from "react";
import { generateAuthCode } from "../services/agentApi";
import styles from "./callcenter.module.css";

const VISIT_TYPES = [
  "Primary Care",
  "Secondary Care",
  "Specialist Consultation",
  "Emergency",
  "Dental",
  "Optical",
  "Pharmacy",
  "Laboratory",
  "Radiology",
  "Physiotherapy",
  "Maternity",
  "Surgery",
  "Other",
];

export default function AuthCodeGenerator({ onCodeGenerated }) {
  const [enrolleeId, setEnrolleeId] = useState("");
  const [approvedAmount, setApprovedAmount] = useState("");
  const [visitType, setVisitType] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!enrolleeId.trim()) {
      setError("Enrollee ID is required");
      return;
    }
    if (!approvedAmount || parseFloat(approvedAmount) <= 0) {
      setError("Valid approved amount is required");
      return;
    }
    if (!visitType) {
      setError("Please select a visit type");
      return;
    }

    setLoading(true);
    try {
      const { data } = await generateAuthCode({
        enrollee_id: enrolleeId.trim(),
        approved_amount: parseFloat(approvedAmount),
        visit_type: visitType,
        notes: notes.trim() || null,
      });
      onCodeGenerated(data);
      // Reset form
      setEnrolleeId("");
      setApprovedAmount("");
      setVisitType("");
      setNotes("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate authorization code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.card}>
      <h3 className={styles.cardTitle}>Generate Authorization Code</h3>
      <p className={styles.cardSubtitle}>
        Create a new authorization code for a member's reimbursement claim
      </p>

      {error && <div className={styles.error}>{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className={styles.formGrid}>
          <label className={styles.label}>
            Enrollee ID *
            <input
              type="text"
              value={enrolleeId}
              onChange={(e) => setEnrolleeId(e.target.value)}
              className={styles.input}
              placeholder="e.g. LWH-001234"
              required
            />
          </label>

          <label className={styles.label}>
            Approved Amount (NGN) *
            <input
              type="number"
              value={approvedAmount}
              onChange={(e) => setApprovedAmount(e.target.value)}
              className={styles.input}
              placeholder="0.00"
              min="0.01"
              step="0.01"
              required
            />
          </label>

          <label className={styles.label}>
            Visit Type *
            <select
              value={visitType}
              onChange={(e) => setVisitType(e.target.value)}
              className={styles.select}
              required
            >
              <option value="">Select visit type...</option>
              {VISIT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          <label className={`${styles.label} ${styles.fullWidth}`}>
            Notes
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className={styles.textarea}
              placeholder="Additional notes about this authorization (optional)"
              rows={3}
            />
          </label>
        </div>

        <button type="submit" disabled={loading} className={styles.generateBtn}>
          {loading ? (
            <>
              <span className={styles.spinner} />
              Generating...
            </>
          ) : (
            "Generate Authorization Code"
          )}
        </button>
      </form>
    </div>
  );
}
