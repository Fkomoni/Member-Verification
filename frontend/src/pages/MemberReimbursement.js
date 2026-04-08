import React, { useState } from "react";
import api from "../services/api";
import sharedStyles from "../components/shared.module.css";
import headerStyles from "./DashboardPage.module.css";

export default function MemberReimbursement() {
  const [mode, setMode] = useState(null); // "code" or "enrollee"
  const [paCode, setPaCode] = useState("");
  const [enrolleeId, setEnrolleeId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Code lookup result
  const [codeResult, setCodeResult] = useState(null);

  // Enrollee lookup results
  const [activeCodes, setActiveCodes] = useState([]);
  const [selectedCode, setSelectedCode] = useState(null);

  // Claim form
  const [claimAmount, setClaimAmount] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  const reset = () => {
    setMode(null);
    setPaCode("");
    setEnrolleeId("");
    setCodeResult(null);
    setActiveCodes([]);
    setSelectedCode(null);
    setClaimAmount("");
    setDescription("");
    setSubmitResult(null);
    setError("");
  };

  const handleCodeLookup = async (e) => {
    e.preventDefault();
    setError("");
    setCodeResult(null);
    setLoading(true);
    try {
      const { data } = await api.get(`/reimbursement/lookup-code?code=${encodeURIComponent(paCode.trim())}`);
      setCodeResult(data);
      setClaimAmount(String(data.approved_amount || ""));
    } catch (err) {
      setError(err.response?.data?.detail || "Authorization code not found");
    } finally {
      setLoading(false);
    }
  };

  const handleEnrolleeLookup = async (e) => {
    e.preventDefault();
    setError("");
    setActiveCodes([]);
    setSelectedCode(null);
    setLoading(true);
    try {
      const { data } = await api.get(`/reimbursement/active-codes?enrollee_id=${encodeURIComponent(enrolleeId.trim())}`);
      if (data.length === 0) {
        setError("No active authorization codes found for this enrollee ID");
      } else {
        setActiveCodes(data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to look up codes");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectCode = (code) => {
    setSelectedCode(code);
    setClaimAmount(String(code.approved_amount || ""));
  };

  const activeCode = codeResult || selectedCode;

  const handleSubmit = async () => {
    if (!activeCode) return;
    setSubmitting(true);
    setError("");
    try {
      const { data } = await api.post("/reimbursement/submit", {
        code: activeCode.code,
        claim_amount: parseFloat(claimAmount) || 0,
        description,
      });
      setSubmitResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit claim");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (d) => d ? d.split("T")[0] : "N/A";

  return (
    <div className={headerStyles.page}>
      {/* Header */}
      <header className={headerStyles.header}>
        <div className={headerStyles.headerLeft}>
          <div className={headerStyles.headerLogo}>
            <svg viewBox="0 0 40 40" width="32" height="32">
              <circle cx="20" cy="20" r="18" fill="url(#hdrGrad3)" />
              <defs>
                <linearGradient id="hdrGrad3" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F15A24" />
                  <stop offset="100%" stopColor="#FFCE07" />
                </linearGradient>
              </defs>
            </svg>
            <div>
              <span className={headerStyles.headerBrand}>LEADWAY</span>
              <span className={headerStyles.headerBrandHealth}> Health</span>
            </div>
          </div>
          <span className={headerStyles.headerDivider} />
          <span className={headerStyles.headerPortal}>Member Reimbursement</span>
        </div>
      </header>

      <main className={headerStyles.main} style={{ maxWidth: 700 }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#263626", marginBottom: "0.25rem" }}>
          Reimbursement Claim
        </h1>
        <p style={{ color: "#777", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
          Submit your reimbursement claim using your authorization code or enrollee ID
        </p>

        {/* Success Result */}
        {submitResult && (
          <div className={sharedStyles.card}>
            <div style={{
              background: "#E8F8EE", border: "2px solid #0A7C3E", borderRadius: 10,
              padding: "1.5rem", textAlign: "center", marginBottom: "1rem"
            }}>
              <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>&#10004;</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#0A7C3E", marginBottom: "0.5rem" }}>
                Claim Submitted Successfully
              </div>
              <div style={{ fontSize: "0.9rem", color: "#444", marginBottom: "0.75rem" }}>
                {submitResult.enrollee_name} &mdash; {submitResult.visit_type_name}
              </div>
              <div style={{ display: "flex", justifyContent: "center", gap: "2rem", flexWrap: "wrap" }}>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>PA Code</span>
                  <div style={{ fontWeight: 800, color: "#0A7C3E", fontSize: "1.1rem" }}>{submitResult.code}</div>
                </div>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Claim Amount</span>
                  <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#263626" }}>NGN {submitResult.claim_amount?.toLocaleString()}</div>
                </div>
              </div>
            </div>
            <button onClick={reset} className={sharedStyles.secondaryBtn}>Submit Another Claim</button>
          </div>
        )}

        {/* Mode Selection */}
        {!submitResult && !mode && (
          <div className={sharedStyles.card}>
            <h2 className={sharedStyles.cardTitle}>How would you like to proceed?</h2>
            <p className={sharedStyles.cardSubtitle}>Choose how to look up your authorization</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <button
                onClick={() => setMode("code")}
                style={{
                  padding: "1rem 1.25rem", borderRadius: 10, border: "1.5px solid #ddd",
                  background: "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.2s",
                }}
                onMouseOver={(e) => { e.currentTarget.style.borderColor = "#C61531"; e.currentTarget.style.background = "#FFF0F0"; }}
                onMouseOut={(e) => { e.currentTarget.style.borderColor = "#ddd"; e.currentTarget.style.background = "#fff"; }}
              >
                <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#263626", marginBottom: "0.25rem" }}>
                  I have an Authorization Code
                </div>
                <div style={{ fontSize: "0.82rem", color: "#777" }}>
                  Enter the PA code provided by the call center (e.g. PA-X7K2-M9R4)
                </div>
              </button>
              <button
                onClick={() => setMode("enrollee")}
                style={{
                  padding: "1rem 1.25rem", borderRadius: 10, border: "1.5px solid #ddd",
                  background: "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.2s",
                }}
                onMouseOver={(e) => { e.currentTarget.style.borderColor = "#C61531"; e.currentTarget.style.background = "#FFF0F0"; }}
                onMouseOut={(e) => { e.currentTarget.style.borderColor = "#ddd"; e.currentTarget.style.background = "#fff"; }}
              >
                <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#263626", marginBottom: "0.25rem" }}>
                  Use my Enrollee ID
                </div>
                <div style={{ fontSize: "0.82rem", color: "#777" }}>
                  Look up active authorization codes using your enrollee ID (e.g. 21000645/0)
                </div>
              </button>
            </div>
          </div>
        )}

        {/* PA Code Lookup */}
        {!submitResult && mode === "code" && !codeResult && (
          <div className={sharedStyles.card}>
            <button onClick={reset} style={{ background: "none", border: "none", color: "#C61531", fontWeight: 600, fontSize: "0.82rem", cursor: "pointer", marginBottom: "1rem", padding: 0 }}>
              &larr; Back
            </button>
            <h2 className={sharedStyles.cardTitle}>Enter Authorization Code</h2>
            <p className={sharedStyles.cardSubtitle}>Enter the PA code provided by the call center</p>
            {error && <div className={sharedStyles.error}>{error}</div>}
            <form onSubmit={handleCodeLookup} className={sharedStyles.row}>
              <input
                type="text"
                placeholder="PA-XXXX-XXXX"
                value={paCode}
                onChange={(e) => setPaCode(e.target.value)}
                required
                className={sharedStyles.input}
                style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}
              />
              <button type="submit" disabled={loading} className={sharedStyles.primaryBtn}>
                {loading ? "Looking up..." : "Look Up"}
              </button>
            </form>
          </div>
        )}

        {/* Enrollee ID Lookup */}
        {!submitResult && mode === "enrollee" && !selectedCode && (
          <div className={sharedStyles.card}>
            <button onClick={reset} style={{ background: "none", border: "none", color: "#C61531", fontWeight: 600, fontSize: "0.82rem", cursor: "pointer", marginBottom: "1rem", padding: 0 }}>
              &larr; Back
            </button>
            <h2 className={sharedStyles.cardTitle}>Enter Enrollee ID</h2>
            <p className={sharedStyles.cardSubtitle}>Look up your active authorization codes</p>
            {error && <div className={sharedStyles.error}>{error}</div>}
            <form onSubmit={handleEnrolleeLookup} className={sharedStyles.row}>
              <input
                type="text"
                placeholder="21000645/0"
                value={enrolleeId}
                onChange={(e) => setEnrolleeId(e.target.value)}
                required
                className={sharedStyles.input}
              />
              <button type="submit" disabled={loading} className={sharedStyles.primaryBtn}>
                {loading ? "Looking up..." : "Look Up"}
              </button>
            </form>

            {/* Active codes list */}
            {activeCodes.length > 0 && (
              <div style={{ marginTop: "1.25rem" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#263626", marginBottom: "0.75rem" }}>
                  Active Authorization Codes ({activeCodes.length})
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {activeCodes.map((c) => (
                    <button
                      key={c.code_id}
                      onClick={() => handleSelectCode(c)}
                      style={{
                        padding: "0.85rem 1rem", borderRadius: 8, border: "1.5px solid #ddd",
                        background: "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.2s",
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                      }}
                      onMouseOver={(e) => { e.currentTarget.style.borderColor = "#C61531"; e.currentTarget.style.background = "#FFF0F0"; }}
                      onMouseOut={(e) => { e.currentTarget.style.borderColor = "#ddd"; e.currentTarget.style.background = "#fff"; }}
                    >
                      <div>
                        <code style={{ fontWeight: 800, color: "#C61531", fontSize: "0.95rem" }}>{c.code}</code>
                        <div style={{ fontSize: "0.78rem", color: "#666", marginTop: "0.2rem" }}>
                          {c.visit_type_name} &mdash; Created {formatDate(c.created_at)}
                        </div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontWeight: 700, color: "#263626", fontSize: "0.95rem" }}>
                          NGN {c.approved_amount?.toLocaleString()}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "#0A7C3E", fontWeight: 600 }}>{c.status}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Claim Form (shown when a code is selected/found) */}
        {!submitResult && activeCode && (
          <div className={sharedStyles.card} style={{ marginTop: mode === "enrollee" ? "1rem" : 0 }}>
            {/* Member info banner */}
            <div style={{
              background: "#E8F8EE", border: "1.5px solid #B5E8C9", borderRadius: 10,
              padding: "1rem 1.25rem", marginBottom: "1.25rem",
            }}>
              <div style={{ color: "#0A7C3E", fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.5rem" }}>
                &#10004; Authorization Verified
              </div>
              <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Name</span>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#263626" }}>{activeCode.enrollee_name}</div>
                </div>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>PA Code</span>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#C61531" }}>{activeCode.code}</div>
                </div>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Visit Type</span>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#263626" }}>{activeCode.visit_type_name}</div>
                </div>
                <div>
                  <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Max Refundable</span>
                  <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0A7C3E" }}>
                    NGN {activeCode.approved_amount?.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            {activeCode.status !== "ACTIVE" && (
              <div className={sharedStyles.error}>
                This authorization code is {activeCode.status} and cannot be used for a new claim.
              </div>
            )}

            {activeCode.status === "ACTIVE" && (
              <>
                <h2 className={sharedStyles.cardTitle}>Submit Claim</h2>
                {error && <div className={sharedStyles.error}>{error}</div>}
                <label className={sharedStyles.label}>
                  Claim Amount (NGN) *
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max={activeCode.approved_amount}
                    placeholder="0.00"
                    value={claimAmount}
                    onChange={(e) => setClaimAmount(e.target.value)}
                    className={sharedStyles.input}
                    style={{ marginTop: "0.25rem" }}
                  />
                  <span style={{ fontSize: "0.75rem", color: "#888", marginTop: "0.25rem", display: "block" }}>
                    Maximum refundable: NGN {activeCode.approved_amount?.toLocaleString()}
                  </span>
                </label>
                <label className={sharedStyles.label}>
                  Description (optional)
                  <textarea
                    placeholder="Brief description of the service received"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className={sharedStyles.input}
                    style={{ marginTop: "0.25rem", minHeight: 80, resize: "vertical" }}
                  />
                </label>
                <button
                  onClick={handleSubmit}
                  disabled={submitting || !claimAmount}
                  className={sharedStyles.primaryBtn}
                >
                  {submitting ? "Submitting..." : "Submit Reimbursement Claim"}
                </button>
              </>
            )}

            <button onClick={reset} className={sharedStyles.secondaryBtn}>
              Start Over
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
