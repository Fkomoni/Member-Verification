import React, { useState } from "react";
import { validateMember } from "../services/memberApi";
import s from "./memberportal.module.css";

export default function MemberValidator({ onValidated }) {
  const [enrolleeId, setEnrolleeId] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!enrolleeId.trim()) return setError("Enrollee ID is required");
    if (!phone.trim()) return setError("Phone number is required");

    setLoading(true);
    try {
      const { data } = await validateMember(enrolleeId.trim(), phone.trim());
      if (data.valid) {
        onValidated({
          enrollee_id: data.enrollee_id || enrolleeId.trim(),
          member_name: data.member_name,
          phone: phone.trim(),
          gender: data.gender,
          plan: data.plan,
        });
      } else {
        setError(data.message || "Verification failed");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.card}>
      <h3 className={s.cardTitle}>Verify Your Identity</h3>
      <p className={s.cardSubtitle}>
        Enter your Enrollee ID and registered phone number to get started
      </p>

      {error && <div className={s.error}>{error}</div>}

      <form onSubmit={handleSubmit}>
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

        <label className={`${s.label} ${s.labelRequired}`}>
          Registered Phone Number
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className={s.input}
            placeholder="e.g. 08012345678"
            required
          />
        </label>

        <button type="submit" disabled={loading} className={s.primaryBtn}>
          {loading ? (
            <>
              <span className={s.spinner} />
              Verifying...
            </>
          ) : (
            "Verify Identity"
          )}
        </button>
      </form>
    </div>
  );
}
