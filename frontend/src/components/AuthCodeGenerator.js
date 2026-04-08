import React, { useState } from "react";
import { generateAuthCode, lookupMember } from "../services/agentApi";
import styles from "./callcenter.module.css";

const FALLBACK_VISIT_TYPES = [
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

  // Member lookup state
  const [memberData, setMemberData] = useState(null);
  const [memberLoading, setMemberLoading] = useState(false);
  const [memberError, setMemberError] = useState("");

  const handleLookupMember = async () => {
    const eid = enrolleeId.trim();
    if (!eid) return;
    if (memberData?.enrollee_id === eid) return; // already loaded

    setMemberLoading(true);
    setMemberError("");
    setMemberData(null);
    try {
      const { data } = await lookupMember(eid);
      setMemberData(data);
    } catch (err) {
      setMemberError(
        err.response?.data?.detail || "Member not found. Check the Enrollee ID."
      );
    } finally {
      setMemberLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!enrolleeId.trim()) return setError("Enrollee ID is required");
    if (!memberData) return setError("Please look up the member first");
    if (!approvedAmount || parseFloat(approvedAmount) <= 0) return setError("Valid approved amount is required");
    if (!visitType) return setError("Please select a visit type");

    setLoading(true);
    try {
      const { data } = await generateAuthCode({
        enrollee_id: enrolleeId.trim(),
        approved_amount: parseFloat(approvedAmount),
        visit_type: visitType,
        notes: notes.trim() || null,
      });
      onCodeGenerated(data);
      setEnrolleeId("");
      setApprovedAmount("");
      setVisitType("");
      setNotes("");
      setMemberData(null);
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
        {/* Enrollee ID with lookup */}
        <div className={styles.formGrid}>
          <label className={styles.label} style={{ gridColumn: "1 / -1" }}>
            Enrollee ID *
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.3rem" }}>
              <input
                type="text"
                value={enrolleeId}
                onChange={(e) => {
                  setEnrolleeId(e.target.value);
                  if (memberData) setMemberData(null);
                }}
                onBlur={handleLookupMember}
                className={styles.input}
                placeholder="e.g. 21000645/0"
                required
                style={{ flex: 1, marginTop: 0 }}
              />
              <button
                type="button"
                onClick={handleLookupMember}
                disabled={memberLoading || !enrolleeId.trim()}
                className={styles.generateBtn}
                style={{ width: "auto", padding: "0.65rem 1.25rem", marginTop: 0 }}
              >
                {memberLoading ? "Looking up..." : "Look Up"}
              </button>
            </div>
          </label>
        </div>

        {/* Member loading */}
        {memberLoading && (
          <div style={{ padding: "0.75rem", color: "#888", fontSize: "0.85rem" }}>
            Looking up member...
          </div>
        )}

        {/* Member error */}
        {memberError && <div className={styles.error}>{memberError}</div>}

        {/* Member details card */}
        {memberData && (
          <div className={styles.memberCard}>
            <div className={styles.memberCardHeader}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0A7C3E" strokeWidth="2.5">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
              <span style={{ color: "#0A7C3E", fontWeight: 700, fontSize: "0.88rem" }}>Member Verified</span>
            </div>
            <div className={styles.memberCardGrid}>
              <div>
                <span className={styles.memberCardLabel}>Full Name</span>
                <span className={styles.memberCardValue}>{memberData.name || "—"}</span>
              </div>
              <div>
                <span className={styles.memberCardLabel}>Enrollee ID</span>
                <span className={styles.memberCardValue}>{memberData.enrollee_id || "—"}</span>
              </div>
              {memberData.company && (
                <div>
                  <span className={styles.memberCardLabel}>Company / Group</span>
                  <span className={styles.memberCardValue}>{memberData.company}</span>
                </div>
              )}
              {memberData.plan && (
                <div>
                  <span className={styles.memberCardLabel}>Scheme / Plan</span>
                  <span className={styles.memberCardValue}>{memberData.plan}</span>
                </div>
              )}
              {memberData.phone && (
                <div>
                  <span className={styles.memberCardLabel}>Phone</span>
                  <span className={styles.memberCardValue}>{memberData.phone}</span>
                </div>
              )}
              {memberData.gender && (
                <div>
                  <span className={styles.memberCardLabel}>Gender</span>
                  <span className={styles.memberCardValue}>{memberData.gender}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Rest of form — only show after member is verified */}
        {memberData && (
          <>
            <div className={styles.formGrid}>
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
                  {FALLBACK_VISIT_TYPES.map((type) => (
                    <option key={type} value={type}>{type}</option>
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
          </>
        )}
      </form>
    </div>
  );
}
