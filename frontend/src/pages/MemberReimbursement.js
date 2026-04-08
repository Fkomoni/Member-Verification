import React, { useState, useEffect } from "react";
import api from "../services/api";
import sharedStyles from "../components/shared.module.css";
import headerStyles from "./DashboardPage.module.css";

export default function MemberReimbursement() {
  const [mode, setMode] = useState(null);
  const [banks, setBanks] = useState([]);
  const [paCode, setPaCode] = useState("");
  const [enrolleeId, setEnrolleeId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [codeResult, setCodeResult] = useState(null);
  const [activeCodes, setActiveCodes] = useState([]);
  const [selectedCode, setSelectedCode] = useState(null);

  // Claim form fields
  const [claimAmount, setClaimAmount] = useState("");
  const [reimbursementReason, setReimbursementReason] = useState("");
  const [providerName, setProviderName] = useState("");
  const [visitDate, setVisitDate] = useState("");
  const [reasonForVisit, setReasonForVisit] = useState("");
  const [remarks, setRemarks] = useState("");

  // Bank details
  const [bankName, setBankName] = useState("");
  const [bankCode, setBankCode] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");
  const [bankValidating, setBankValidating] = useState(false);
  const [bankValidated, setBankValidated] = useState(false);
  const [bankError, setBankError] = useState("");

  // File uploads
  const [receipts, setReceipts] = useState([]);
  const [medicalReport, setMedicalReport] = useState(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  useEffect(() => {
    api.get("/reimbursement/banks").then(({ data }) => {
      if (data.success) setBanks(data.banks);
    }).catch(() => {});
  }, []);

  const reset = () => {
    setMode(null); setPaCode(""); setEnrolleeId(""); setCodeResult(null);
    setActiveCodes([]); setSelectedCode(null); setClaimAmount("");
    setReimbursementReason(""); setProviderName(""); setVisitDate("");
    setReasonForVisit(""); setRemarks(""); setBankName(""); setBankCode("");
    setAccountNumber(""); setAccountName(""); setBankValidated(false);
    setBankError(""); setReceipts([]);
    setMedicalReport(null); setSubmitResult(null); setError("");
  };

  const handleCodeLookup = async (e) => {
    e.preventDefault();
    setError(""); setCodeResult(null); setLoading(true);
    try {
      const { data } = await api.get(`/reimbursement/lookup-code?code=${encodeURIComponent(paCode.trim())}`);
      setCodeResult(data);
      setClaimAmount(String(data.approved_amount || ""));
    } catch (err) {
      setError(err.response?.data?.detail || "Authorization code not found");
    } finally { setLoading(false); }
  };

  const handleEnrolleeLookup = async (e) => {
    e.preventDefault();
    setError(""); setActiveCodes([]); setSelectedCode(null); setLoading(true);
    try {
      const { data } = await api.get(`/reimbursement/active-codes?enrollee_id=${encodeURIComponent(enrolleeId.trim())}`);
      if (data.length === 0) setError("No active authorization codes found for this enrollee ID");
      else setActiveCodes(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to look up codes");
    } finally { setLoading(false); }
  };

  const handleSelectCode = (code) => {
    setSelectedCode(code);
    setClaimAmount(String(code.approved_amount || ""));
  };

  const activeCode = codeResult || selectedCode;

  const fileToBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const handleValidateBank = async () => {
    if (!accountNumber || !bankCode) return;
    setBankValidating(true);
    setBankError("");
    setBankValidated(false);
    try {
      const { data } = await api.post("/reimbursement/validate-bank", {
        account_number: accountNumber,
        bank_code: bankCode,
      });
      if (data.validated) {
        setAccountName(data.account_name || "");
        setBankValidated(true);
      } else {
        setBankError(data.reason || "Could not validate bank account");
      }
    } catch {
      setBankError("Bank validation service unavailable");
    } finally { setBankValidating(false); }
  };

  const handleSubmit = async () => {
    if (!activeCode || !reasonForVisit || !providerName || !visitDate) {
      setError("Please fill in all required fields");
      return;
    }
    setSubmitting(true); setError("");
    try {
      // Convert files to base64
      const claimDocuments = [];
      for (const file of receipts) {
        const b64 = await fileToBase64(file);
        claimDocuments.push({
          ClaimDocument: b64,
          claimContentType: file.type.includes("pdf") ? "pdf" : "image",
          DocumentCategory: "Claims",
        });
      }
      if (medicalReport) {
        const b64 = await fileToBase64(medicalReport);
        claimDocuments.push({
          ClaimDocument: b64,
          claimContentType: medicalReport.type.includes("pdf") ? "pdf" : "image",
          DocumentCategory: "MedicalReport",
        });
      }

      const { data } = await api.post("/reimbursement/submit", {
        code: activeCode.code,
        claim_amount: parseFloat(claimAmount) || 0,
        reimbursement_reason: reimbursementReason,
        provider_name: providerName,
        visit_date: visitDate,
        reason_for_visit: reasonForVisit,
        remarks,
        bank_name: bankName,
        account_number: accountNumber,
        account_name: accountName,
        claim_documents: claimDocuments,
      });
      setSubmitResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit claim");
    } finally { setSubmitting(false); }
  };

  const formatDate = (d) => d ? d.split("T")[0] : "N/A";

  const isSecondary = activeCode && ["Inpatient", "Major Disease Benefit", "Maternity"].includes(activeCode.visit_type_name?.trim());

  return (
    <div className={headerStyles.page}>
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

      <main className={headerStyles.main} style={{ maxWidth: 750 }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#263626", marginBottom: "0.25rem" }}>
          Reimbursement Claim
        </h1>
        <p style={{ color: "#777", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
          Submit your reimbursement claim using your authorization code or enrollee ID
        </p>

        {/* ── Success Result ── */}
        {submitResult && (
          <div className={sharedStyles.card}>
            <div style={{ background: "#E8F8EE", border: "2px solid #0A7C3E", borderRadius: 10, padding: "1.5rem", textAlign: "center", marginBottom: "1rem" }}>
              <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>&#10004;</div>
              <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "#0A7C3E", marginBottom: "0.5rem" }}>Claim Submitted Successfully</div>
              <div style={{ fontSize: "0.9rem", color: "#444", marginBottom: "0.75rem" }}>
                {submitResult.enrollee_name} &mdash; {submitResult.visit_type_name}
              </div>
              <div style={{ display: "flex", justifyContent: "center", gap: "2rem", flexWrap: "wrap" }}>
                <div>
                  <span style={labelMini}>PA Code</span>
                  <div style={{ fontWeight: 800, color: "#0A7C3E", fontSize: "1.1rem" }}>{submitResult.code}</div>
                </div>
                <div>
                  <span style={labelMini}>Claim Amount</span>
                  <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#263626" }}>NGN {submitResult.claim_amount?.toLocaleString()}</div>
                </div>
                <div>
                  <span style={labelMini}>Provider</span>
                  <div style={{ fontWeight: 600, color: "#263626" }}>{submitResult.provider_name}</div>
                </div>
              </div>
            </div>
            <button onClick={reset} className={sharedStyles.secondaryBtn}>Submit Another Claim</button>
          </div>
        )}

        {/* ── Mode Selection ── */}
        {!submitResult && !mode && (
          <div className={sharedStyles.card}>
            <h2 className={sharedStyles.cardTitle}>How would you like to proceed?</h2>
            <p className={sharedStyles.cardSubtitle}>Choose how to look up your authorization</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <ModeButton onClick={() => setMode("code")} title="I have an Authorization Code" subtitle="Enter the PA code provided by the call center (e.g. PA-X7K2-M9R4)" />
              <ModeButton onClick={() => setMode("enrollee")} title="Use my Enrollee ID" subtitle="Look up active authorization codes using your enrollee ID (e.g. 21000645/0)" />
            </div>
          </div>
        )}

        {/* ── PA Code Lookup ── */}
        {!submitResult && mode === "code" && !codeResult && (
          <div className={sharedStyles.card}>
            <BackBtn onClick={reset} />
            <h2 className={sharedStyles.cardTitle}>Enter Authorization Code</h2>
            <p className={sharedStyles.cardSubtitle}>Enter the PA code provided by the call center</p>
            {error && <div className={sharedStyles.error}>{error}</div>}
            <form onSubmit={handleCodeLookup} className={sharedStyles.row}>
              <input type="text" placeholder="PA-XXXX-XXXX" value={paCode} onChange={(e) => setPaCode(e.target.value)} required className={sharedStyles.input} style={{ textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }} />
              <button type="submit" disabled={loading} className={sharedStyles.primaryBtn}>{loading ? "Looking up..." : "Look Up"}</button>
            </form>
          </div>
        )}

        {/* ── Enrollee ID Lookup ── */}
        {!submitResult && mode === "enrollee" && !selectedCode && (
          <div className={sharedStyles.card}>
            <BackBtn onClick={reset} />
            <h2 className={sharedStyles.cardTitle}>Enter Enrollee ID</h2>
            <p className={sharedStyles.cardSubtitle}>Look up your active authorization codes</p>
            {error && <div className={sharedStyles.error}>{error}</div>}
            <form onSubmit={handleEnrolleeLookup} className={sharedStyles.row}>
              <input type="text" placeholder="21000645/0" value={enrolleeId} onChange={(e) => setEnrolleeId(e.target.value)} required className={sharedStyles.input} />
              <button type="submit" disabled={loading} className={sharedStyles.primaryBtn}>{loading ? "Looking up..." : "Look Up"}</button>
            </form>
            {activeCodes.length > 0 && (
              <div style={{ marginTop: "1.25rem" }}>
                <h3 style={{ fontSize: "0.9rem", fontWeight: 700, color: "#263626", marginBottom: "0.75rem" }}>Active Authorization Codes ({activeCodes.length})</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {activeCodes.map((c) => (
                    <button key={c.code_id} onClick={() => handleSelectCode(c)} style={{ padding: "0.85rem 1rem", borderRadius: 8, border: "1.5px solid #ddd", background: "#fff", cursor: "pointer", textAlign: "left", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <code style={{ fontWeight: 800, color: "#C61531", fontSize: "0.95rem" }}>{c.code}</code>
                        <div style={{ fontSize: "0.78rem", color: "#666", marginTop: "0.2rem" }}>{c.visit_type_name} — Created {formatDate(c.created_at)}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontWeight: 700, color: "#263626" }}>NGN {c.approved_amount?.toLocaleString()}</div>
                        <div style={{ fontSize: "0.72rem", color: "#0A7C3E", fontWeight: 600 }}>{c.status}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Full Claim Form ── */}
        {!submitResult && activeCode && (
          <div className={sharedStyles.card} style={{ marginTop: mode === "enrollee" && selectedCode ? "1rem" : 0 }}>
            {/* Authorization banner */}
            <div style={{ background: "#E8F8EE", border: "1.5px solid #B5E8C9", borderRadius: 10, padding: "1rem 1.25rem", marginBottom: "1.25rem" }}>
              <div style={{ color: "#0A7C3E", fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.5rem" }}>&#10004; Authorization Verified</div>
              <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
                <InfoChip label="Name" value={activeCode.enrollee_name} />
                <InfoChip label="PA Code" value={activeCode.code} color="#C61531" />
                <InfoChip label="Visit Type" value={activeCode.visit_type_name} />
                <InfoChip label="Max Refundable" value={`NGN ${activeCode.approved_amount?.toLocaleString()}`} color="#0A7C3E" bold />
              </div>
            </div>

            {activeCode.status !== "ACTIVE" ? (
              <div className={sharedStyles.error}>This authorization code is {activeCode.status} and cannot be used for a new claim.</div>
            ) : (
              <>
                <h2 className={sharedStyles.cardTitle}>Claim Details</h2>
                {error && <div className={sharedStyles.error}>{error}</div>}

                {/* Row 1: Amount + Visit Date */}
                <div style={rowStyle}>
                  <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                    Claim Amount (NGN) *
                    <input type="number" step="0.01" min="0" max={activeCode.approved_amount} value={claimAmount} onChange={(e) => setClaimAmount(e.target.value)} className={sharedStyles.input} style={{ marginTop: "0.25rem" }} />
                    <span style={{ fontSize: "0.75rem", color: "#888", display: "block", marginTop: "0.2rem" }}>Max: NGN {activeCode.approved_amount?.toLocaleString()}</span>
                  </label>
                  <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                    Visit Date *
                    <input type="date" value={visitDate} onChange={(e) => setVisitDate(e.target.value)} required className={sharedStyles.input} style={{ marginTop: "0.25rem" }} />
                  </label>
                </div>

                {/* Row 2: Provider + Reimbursement Reason */}
                <div style={rowStyle}>
                  <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                    Healthcare Provider Name *
                    <input type="text" placeholder="Hospital, Lab, or Pharmacy name" value={providerName} onChange={(e) => setProviderName(e.target.value)} required className={sharedStyles.input} style={{ marginTop: "0.25rem" }} />
                  </label>
                  <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                    Reimbursement Reason
                    <select value={reimbursementReason} onChange={(e) => setReimbursementReason(e.target.value)} className={sharedStyles.input} style={{ marginTop: "0.25rem" }}>
                      <option value="">Select reason...</option>
                      <option value="No provider nearby">No provider nearby</option>
                      <option value="Emergency treatment">Emergency treatment</option>
                      <option value="Specialist referral">Specialist referral</option>
                      <option value="Medication purchase">Medication purchase</option>
                      <option value="Lab/Diagnostic test">Lab/Diagnostic test</option>
                      <option value="Other">Other</option>
                    </select>
                  </label>
                </div>

                {/* Reason for Visit */}
                <label className={sharedStyles.label}>
                  Reason for Visit *
                  <textarea placeholder="Describe the reason for the hospital/clinic visit" value={reasonForVisit} onChange={(e) => setReasonForVisit(e.target.value)} required className={sharedStyles.input} style={{ marginTop: "0.25rem", minHeight: 70, resize: "vertical" }} />
                </label>

                {/* Comments / Remarks */}
                <label className={sharedStyles.label}>
                  Comments / Remarks
                  <textarea placeholder="Additional comments (optional)" value={remarks} onChange={(e) => setRemarks(e.target.value)} className={sharedStyles.input} style={{ marginTop: "0.25rem", minHeight: 60, resize: "vertical" }} />
                </label>

                {/* File Uploads */}
                <div style={rowStyle}>
                  <label className={sharedStyles.label} style={{ flex: 1 }}>
                    Upload Receipts *
                    <input type="file" multiple accept="image/*,.pdf" onChange={(e) => setReceipts(Array.from(e.target.files))} className={sharedStyles.input} style={{ marginTop: "0.25rem", padding: "0.5rem" }} />
                    <span style={{ fontSize: "0.72rem", color: "#888" }}>PDF or image files. You can select multiple.</span>
                  </label>
                  <label className={sharedStyles.label} style={{ flex: 1 }}>
                    Medical Report {isSecondary && <span style={{ color: "#C61531" }}>* (Required)</span>}
                    <input type="file" accept="image/*,.pdf" onChange={(e) => setMedicalReport(e.target.files[0] || null)} className={sharedStyles.input} style={{ marginTop: "0.25rem", padding: "0.5rem" }} />
                    <span style={{ fontSize: "0.72rem", color: "#888" }}>Required for secondary care (Inpatient, Maternity, etc.)</span>
                  </label>
                </div>

                {/* Bank Details */}
                <div style={{ borderTop: "1px solid #eee", paddingTop: "1rem", marginTop: "0.5rem" }}>
                  <h3 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#263626", marginBottom: "0.75rem" }}>Bank Details for Payment</h3>
                  <div style={rowStyle}>
                    <label className={sharedStyles.label} style={{ flex: 1, minWidth: 180 }}>
                      Bank Name *
                      <select value={bankCode} onChange={(e) => {
                        const selected = banks.find(b => b.code === e.target.value);
                        setBankCode(e.target.value);
                        setBankName(selected ? selected.name : "");
                        setBankValidated(false); setAccountName(""); setBankError("");
                      }} required className={sharedStyles.input} style={{ marginTop: "0.25rem" }}>
                        <option value="">Select bank...</option>
                        {(banks.length > 0 ? banks : BANKS.map(b => ({ name: b, code: b }))).map((b) => (
                          <option key={b.code} value={b.code}>{b.name}</option>
                        ))}
                      </select>
                    </label>
                    <label className={sharedStyles.label} style={{ flex: 1, minWidth: 180 }}>
                      Account Number *
                      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
                        <input type="text" maxLength={10} placeholder="0123456789" value={accountNumber} onChange={(e) => { setAccountNumber(e.target.value); setBankValidated(false); }} required className={sharedStyles.input} />
                        <button type="button" onClick={handleValidateBank} disabled={bankValidating || accountNumber.length < 10 || !bankCode} className={sharedStyles.primaryBtn} style={{ padding: "0.5rem 0.8rem", fontSize: "0.78rem", whiteSpace: "nowrap" }}>
                          {bankValidating ? "Verifying..." : "Verify"}
                        </button>
                      </div>
                    </label>
                  </div>
                  <label className={sharedStyles.label}>
                    Account Name
                    <input type="text" value={accountName} onChange={(e) => setAccountName(e.target.value)} placeholder="Account holder name" className={sharedStyles.input} style={{ marginTop: "0.25rem", background: bankValidated ? "#E8F8EE" : "#fff" }} />
                    {bankValidated && <span style={{ fontSize: "0.75rem", color: "#0A7C3E", fontWeight: 600 }}>&#10004; Account Verified</span>}
                    {bankError && <span style={{ fontSize: "0.75rem", color: "#C61531", fontWeight: 600 }}>{bankError}</span>}
                  </label>
                </div>

                {/* Submit */}
                <button onClick={handleSubmit} disabled={submitting || !claimAmount || !reasonForVisit || !providerName || !visitDate || !accountNumber || receipts.length === 0} className={sharedStyles.primaryBtn} style={{ marginTop: "0.75rem", width: "100%" }}>
                  {submitting ? "Submitting Claim..." : "Submit Reimbursement Claim"}
                </button>
              </>
            )}
            <button onClick={reset} className={sharedStyles.secondaryBtn} style={{ width: "100%" }}>Start Over</button>
          </div>
        )}
      </main>
    </div>
  );
}

// ── Helpers ──

const labelMini = { fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600, display: "block" };
const rowStyle = { display: "flex", gap: "1rem", marginBottom: "0.25rem", flexWrap: "wrap" };

function InfoChip({ label, value, color, bold }) {
  return (
    <div>
      <span style={labelMini}>{label}</span>
      <div style={{ fontWeight: bold ? 800 : 700, fontSize: bold ? "1.1rem" : "0.95rem", color: color || "#263626" }}>{value}</div>
    </div>
  );
}

function ModeButton({ onClick, title, subtitle }) {
  return (
    <button onClick={onClick} style={{ padding: "1rem 1.25rem", borderRadius: 10, border: "1.5px solid #ddd", background: "#fff", cursor: "pointer", textAlign: "left", transition: "all 0.2s" }}
      onMouseOver={(e) => { e.currentTarget.style.borderColor = "#C61531"; e.currentTarget.style.background = "#FFF0F0"; }}
      onMouseOut={(e) => { e.currentTarget.style.borderColor = "#ddd"; e.currentTarget.style.background = "#fff"; }}>
      <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#263626", marginBottom: "0.25rem" }}>{title}</div>
      <div style={{ fontSize: "0.82rem", color: "#777" }}>{subtitle}</div>
    </button>
  );
}

function BackBtn({ onClick }) {
  return <button onClick={onClick} style={{ background: "none", border: "none", color: "#C61531", fontWeight: 600, fontSize: "0.82rem", cursor: "pointer", marginBottom: "1rem", padding: 0 }}>&larr; Back</button>;
}

const BANKS = [
  "ACCESS BANK PLC", "CITIBANK NIGERIA LIMITED", "ECOBANK NIGERIA PLC",
  "FIDELITY BANK PLC", "FIRST BANK OF NIGERIA LIMITED", "FIRST CITY MONUMENT BANK PLC",
  "GLOBUS BANK LIMITED", "GUARANTY TRUST BANK PLC", "HERITAGE BANK PLC",
  "JAIZ BANK PLC", "KEYSTONE BANK LIMITED", "KUDA MICROFINANCE BANK",
  "LOTUS BANK LIMITED", "OPAY", "PALMPAY",
  "POLARIS BANK LIMITED", "PROVIDUS BANK LIMITED", "STANBIC IBTC BANK PLC",
  "STANDARD CHARTERED BANK", "STERLING BANK PLC", "SUNTRUST BANK NIGERIA LIMITED",
  "TAJ BANK LIMITED", "TITAN TRUST BANK LIMITED", "UNION BANK OF NIGERIA PLC",
  "UNITED BANK FOR AFRICA PLC", "UNITY BANK PLC", "VFD MICROFINANCE BANK",
  "WEMA BANK PLC", "ZENITH BANK PLC",
];
