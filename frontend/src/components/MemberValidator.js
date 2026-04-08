import React, { useState } from "react";
import { validateMember } from "../services/memberApi";
import s from "./memberportal.module.css";

export default function MemberValidator({ onValidated }) {
  const [enrolleeId, setEnrolleeId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [foundMember, setFoundMember] = useState(null);

  const handleLookup = async (e) => {
    e.preventDefault();
    setError("");
    setFoundMember(null);

    if (!enrolleeId.trim()) return setError("Enrollee ID is required");

    setLoading(true);
    try {
      const { data } = await validateMember(enrolleeId.trim());
      if (data.valid) {
        setFoundMember({
          enrollee_id: data.enrollee_id || enrolleeId.trim(),
          member_name: data.member_name,
          gender: data.gender,
          plan: data.plan,
        });
      } else {
        setError(data.message || "Member not found");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Lookup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    onValidated(foundMember);
  };

  const handleTryAnother = () => {
    setFoundMember(null);
    setEnrolleeId("");
    setError("");
  };

  return (
    <div className={s.card}>
      <h3 className={s.cardTitle}>Verify Your Identity</h3>
      <p className={s.cardSubtitle}>
        Enter your Enrollee ID to look up your membership
      </p>

      {error && <div className={s.error}>{error}</div>}

      {!foundMember ? (
        <form onSubmit={handleLookup}>
          <label className={`${s.label} ${s.labelRequired}`}>
            Enrollee ID
            <input
              type="text"
              value={enrolleeId}
              onChange={(e) => setEnrolleeId(e.target.value)}
              className={s.input}
              placeholder="e.g. LWH-001234"
              required
            />
          </label>

          <button type="submit" disabled={loading} className={s.primaryBtn}>
            {loading ? (
              <>
                <span className={s.spinner} />
                Looking up...
              </>
            ) : (
              "Look Up Member"
            )}
          </button>
        </form>
      ) : (
        <div>
          <div className={s.successBanner}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            Member found
          </div>

          <div className={s.memberBar}>
            <div className={s.memberBarItem}>
              <span className={s.memberBarLabel}>Full Name</span>
              <span className={s.memberBarValue}>{foundMember.member_name}</span>
            </div>
            <div className={s.memberBarItem}>
              <span className={s.memberBarLabel}>Enrollee ID</span>
              <span className={s.memberBarValue}>{foundMember.enrollee_id}</span>
            </div>
            {foundMember.gender && (
              <div className={s.memberBarItem}>
                <span className={s.memberBarLabel}>Gender</span>
                <span className={s.memberBarValue}>{foundMember.gender}</span>
              </div>
            )}
            {foundMember.plan && (
              <div className={s.memberBarItem}>
                <span className={s.memberBarLabel}>Plan</span>
                <span className={s.memberBarValue}>{foundMember.plan}</span>
              </div>
            )}
          </div>

          <p style={{ fontSize: "0.9rem", color: "#555", marginBottom: "1.25rem", lineHeight: 1.6 }}>
            Is this your account? Confirm to proceed, or enter a different Enrollee ID.
          </p>

          <div className={s.btnRow}>
            <button type="button" onClick={handleTryAnother} className={s.secondaryBtn}>
              Not Me — Try Another ID
            </button>
            <button type="button" onClick={handleConfirm} className={s.primaryBtn} style={{ flex: 1 }}>
              Yes, That's Me — Continue
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
