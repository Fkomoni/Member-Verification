import React, { useState } from "react";
import { validateAuthCode } from "../services/memberApi";
import s from "./memberportal.module.css";

export default function AuthCodeValidator({ memberData, onValidated, onBack }) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const formatAmount = (amount) =>
    new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
    }).format(amount);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!code.trim()) return setError("Authorization code is required");

    setLoading(true);
    try {
      const { data } = await validateAuthCode(
        code.trim().toUpperCase(),
        memberData.enrollee_id
      );
      if (data.valid) {
        onValidated({
          code: data.code,
          approved_amount: data.approved_amount,
          visit_type: data.visit_type,
          expires_at: data.expires_at,
          member_name: data.member_name || memberData.member_name,
        });
      } else {
        setError(data.message || "Invalid authorization code");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Code validation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.card}>
      <h3 className={s.cardTitle}>Enter Authorization Code</h3>
      <p className={s.cardSubtitle}>
        Enter the authorization code provided by the call center agent
      </p>

      {/* Member info bar */}
      <div className={s.memberBar}>
        <div className={s.memberBarItem}>
          <span className={s.memberBarLabel}>Member</span>
          <span className={s.memberBarValue}>{memberData.member_name}</span>
        </div>
        <div className={s.memberBarItem}>
          <span className={s.memberBarLabel}>Enrollee ID</span>
          <span className={s.memberBarValue}>{memberData.enrollee_id}</span>
        </div>
        {memberData.plan && (
          <div className={s.memberBarItem}>
            <span className={s.memberBarLabel}>Plan</span>
            <span className={s.memberBarValue}>{memberData.plan}</span>
          </div>
        )}
      </div>

      {error && <div className={s.error}>{error}</div>}

      <form onSubmit={handleSubmit}>
        <label className={`${s.label} ${s.labelRequired}`}>
          Authorization Code
          <input
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            className={s.input}
            placeholder="e.g. LH-ABCD-EFGH"
            style={{ fontFamily: '"Courier New", monospace', fontWeight: 700, letterSpacing: "0.08em", fontSize: "1.1rem" }}
            maxLength={14}
            required
          />
        </label>

        <div className={s.info}>
          This code was provided during your call with our authorization center.
          Codes are single-use and time-limited.
        </div>

        <div className={s.btnRow}>
          <button type="button" onClick={onBack} className={s.secondaryBtn}>
            Back
          </button>
          <button type="submit" disabled={loading} className={s.primaryBtn} style={{ flex: 1 }}>
            {loading ? (
              <>
                <span className={s.spinner} />
                Validating...
              </>
            ) : (
              "Validate Code"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
