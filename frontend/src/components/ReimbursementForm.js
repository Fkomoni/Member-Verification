import React, { useState, useEffect, useRef } from "react";
import { getBankList, validateBank, submitReimbursement } from "../services/memberApi";
import s from "./memberportal.module.css";

const EMPTY_LINE = { service_name: "", quantity: 1, unit_price: "" };

export default function ReimbursementForm({ memberData, codeData, onSubmitted, onBack }) {
  // -- Contact
  const [memberPhone, setMemberPhone] = useState("");

  // -- Form state
  const [reimbursementReason, setReimbursementReason] = useState("");
  const [hospitalName, setHospitalName] = useState("");
  const [visitDate, setVisitDate] = useState("");
  const [reasonForVisit, setReasonForVisit] = useState("");
  const [claimAmount, setClaimAmount] = useState("");
  const [medications, setMedications] = useState("");
  const [labInvestigations, setLabInvestigations] = useState("");
  const [comments, setComments] = useState("");

  // -- Service lines
  const [serviceLines, setServiceLines] = useState([{ ...EMPTY_LINE }]);

  // -- Bank
  const [banks, setBanks] = useState([]);
  const [bankName, setBankName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");
  const [bankValidating, setBankValidating] = useState(false);

  // -- Documents
  const [receipts, setReceipts] = useState([]);
  const [medicalReport, setMedicalReport] = useState([]);
  const receiptRef = useRef(null);
  const reportRef = useRef(null);

  // -- UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isSecondaryCare = codeData.visit_type?.toLowerCase().includes("secondary") ||
    codeData.visit_type?.toLowerCase().includes("specialist") ||
    codeData.visit_type?.toLowerCase().includes("surgery");

  // Load bank list
  useEffect(() => {
    getBankList()
      .then(({ data }) => setBanks(data.banks))
      .catch(() => {});
  }, []);

  // Validate bank account when account number is 10 digits
  useEffect(() => {
    if (bankName && accountNumber.length === 10) {
      setBankValidating(true);
      validateBank(bankName, accountNumber)
        .then(({ data }) => {
          if (data.valid) setAccountName(data.account_name || "");
        })
        .catch(() => {})
        .finally(() => setBankValidating(false));
    }
  }, [bankName, accountNumber]);

  const formatAmount = (amount) =>
    new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" }).format(amount);

  // -- Service line helpers
  const updateLine = (idx, field, value) => {
    setServiceLines((prev) =>
      prev.map((line, i) => (i === idx ? { ...line, [field]: value } : line))
    );
  };

  const addLine = () => setServiceLines((prev) => [...prev, { ...EMPTY_LINE }]);

  const removeLine = (idx) => {
    if (serviceLines.length <= 1) return;
    setServiceLines((prev) => prev.filter((_, i) => i !== idx));
  };

  const lineTotal = (line) => (line.quantity || 0) * (parseFloat(line.unit_price) || 0);
  const grandTotal = serviceLines.reduce((sum, l) => sum + lineTotal(l), 0);

  // -- File helpers
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  const handleReceiptFiles = (e) => {
    const files = Array.from(e.target.files || []);
    setReceipts((prev) => [...prev, ...files]);
  };

  const handleReportFiles = (e) => {
    const files = Array.from(e.target.files || []);
    setMedicalReport((prev) => [...prev, ...files]);
  };

  // -- Submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!memberPhone.trim()) return setError("Phone number is required");
    if (!reimbursementReason.trim()) return setError("Reimbursement reason is required");
    if (!hospitalName.trim()) return setError("Hospital name is required");
    if (!visitDate) return setError("Visit date is required");
    if (!reasonForVisit.trim()) return setError("Reason for visit is required");
    if (!claimAmount || parseFloat(claimAmount) <= 0) return setError("Valid claim amount is required");
    if (!bankName) return setError("Bank name is required");
    if (!accountNumber || accountNumber.length !== 10) return setError("Valid 10-digit account number is required");
    if (!accountName.trim()) return setError("Account name is required");
    if (receipts.length === 0) return setError("At least one receipt is required");
    if (isSecondaryCare && medicalReport.length === 0) return setError("Medical report is required for secondary care");

    // Build valid service lines (skip empty ones)
    const validLines = serviceLines.filter(
      (l) => l.service_name.trim() && l.quantity > 0 && parseFloat(l.unit_price) > 0
    );

    setLoading(true);
    try {
      const formPayload = {
        authorization_code: codeData.code,
        enrollee_id: memberData.enrollee_id,
        member_phone: memberPhone.trim(),
        hospital_name: hospitalName.trim(),
        visit_date: visitDate,
        reason_for_visit: reasonForVisit.trim(),
        reimbursement_reason: reimbursementReason.trim(),
        claim_amount: parseFloat(claimAmount),
        medications: medications.trim() || null,
        lab_investigations: labInvestigations.trim() || null,
        comments: comments.trim() || null,
        bank_name: bankName,
        account_number: accountNumber,
        account_name: accountName.trim(),
        service_lines: validLines.map((l) => ({
          service_name: l.service_name.trim(),
          quantity: parseInt(l.quantity),
          unit_price: parseFloat(l.unit_price),
        })),
      };

      const { data } = await submitReimbursement(formPayload, receipts, medicalReport);

      if (data.success) {
        onSubmitted({
          claim_id: data.claim_id,
          claim_ref: data.claim_ref,
          message: data.message,
        });
      } else {
        setError(data.message || "Submission failed");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.card}>
      <h3 className={s.cardTitle}>Reimbursement Claim Form</h3>
      <p className={s.cardSubtitle}>Complete all required fields to submit your claim</p>

      {/* Member + Code bar */}
      <div className={s.memberBar}>
        <div className={s.memberBarItem}>
          <span className={s.memberBarLabel}>Member</span>
          <span className={s.memberBarValue}>{memberData.member_name}</span>
        </div>
        <div className={s.memberBarItem}>
          <span className={s.memberBarLabel}>Enrollee ID</span>
          <span className={s.memberBarValue}>{memberData.enrollee_id}</span>
        </div>
      </div>

      <div className={s.codeValidated}>
        <div>
          <div className={s.codeValidatedLabel}>Authorization Code</div>
          <div className={s.codeValidatedValue}>{codeData.code}</div>
        </div>
        <div className={s.codeValidatedAmount}>
          <div className={s.codeAmountLabel}>Approved Amount</div>
          <div className={s.codeAmountValue}>{formatAmount(codeData.approved_amount)}</div>
        </div>
      </div>

      {error && <div className={s.error}>{error}</div>}

      <form onSubmit={handleSubmit}>
        {/* ── Contact ─────────────────────────── */}
        <h4 className={s.sectionTitle}>Contact Information</h4>
        <p className={s.sectionSubtitle}>Provide your phone number so we can reach you</p>

        <label className={`${s.label} ${s.labelRequired}`}>
          Phone Number
          <input
            type="tel"
            value={memberPhone}
            onChange={(e) => setMemberPhone(e.target.value)}
            className={s.input}
            placeholder="e.g. 08012345678"
            required
          />
        </label>

        <hr className={s.sectionDivider} />

        {/* ── Claim Details ──────────────────────── */}
        <h4 className={s.sectionTitle}>Claim Details</h4>
        <p className={s.sectionSubtitle}>Provide the details of your healthcare visit</p>

        <div className={s.formGrid}>
          <label className={`${s.label} ${s.labelRequired} ${s.fullWidth}`}>
            Reimbursement Reason
            <textarea
              value={reimbursementReason}
              onChange={(e) => setReimbursementReason(e.target.value)}
              className={s.textarea}
              placeholder="Why are you requesting reimbursement?"
              rows={2}
              required
            />
          </label>

          <label className={`${s.label} ${s.labelRequired}`}>
            Hospital / Facility Name
            <input
              type="text"
              value={hospitalName}
              onChange={(e) => setHospitalName(e.target.value)}
              className={s.input}
              placeholder="Name of hospital or clinic"
              required
            />
          </label>

          <label className={`${s.label} ${s.labelRequired}`}>
            Visit Date
            <input
              type="date"
              value={visitDate}
              onChange={(e) => setVisitDate(e.target.value)}
              className={s.input}
              max={new Date().toISOString().split("T")[0]}
              required
            />
          </label>

          <label className={`${s.label} ${s.labelRequired} ${s.fullWidth}`}>
            Reason for Visit
            <textarea
              value={reasonForVisit}
              onChange={(e) => setReasonForVisit(e.target.value)}
              className={s.textarea}
              placeholder="Describe the medical condition or reason for your visit"
              rows={2}
              required
            />
          </label>

          <label className={`${s.label} ${s.labelRequired}`}>
            Claim Amount (NGN)
            <input
              type="number"
              value={claimAmount}
              onChange={(e) => setClaimAmount(e.target.value)}
              className={s.input}
              placeholder="0.00"
              min="0.01"
              step="0.01"
              required
            />
          </label>

          {claimAmount && parseFloat(claimAmount) > parseFloat(codeData.approved_amount) && (
            <div className={`${s.warningBanner} ${s.fullWidth}`}>
              Claim amount exceeds the approved amount of {formatAmount(codeData.approved_amount)}.
              This will be flagged for review.
            </div>
          )}

          <label className={s.label}>
            Medications Purchased
            <textarea
              value={medications}
              onChange={(e) => setMedications(e.target.value)}
              className={s.textarea}
              placeholder="List medications purchased (optional)"
              rows={2}
            />
          </label>

          <label className={s.label}>
            Lab Investigations
            <textarea
              value={labInvestigations}
              onChange={(e) => setLabInvestigations(e.target.value)}
              className={s.textarea}
              placeholder="List lab tests done (optional)"
              rows={2}
            />
          </label>

          <label className={`${s.label} ${s.fullWidth}`}>
            Additional Comments
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className={s.textarea}
              placeholder="Any additional information (optional)"
              rows={2}
            />
          </label>
        </div>

        {/* ── Service Lines ──────────────────────── */}
        <hr className={s.sectionDivider} />
        <h4 className={s.sectionTitle}>Services Rendered</h4>
        <p className={s.sectionSubtitle}>Add each service, quantity, and price</p>

        <div className={s.serviceLines}>
          <div className={s.serviceLineHeader}>
            <span className={s.serviceLineHeaderCell}>Service</span>
            <span className={s.serviceLineHeaderCell}>Qty</span>
            <span className={s.serviceLineHeaderCell}>Unit Price</span>
            <span className={s.serviceLineHeaderCell}>Total</span>
            <span />
          </div>

          {serviceLines.map((line, idx) => (
            <div key={idx} className={s.serviceLine}>
              <input
                type="text"
                value={line.service_name}
                onChange={(e) => updateLine(idx, "service_name", e.target.value)}
                className={`${s.input} ${s.inputSmall}`}
                placeholder="Service name"
              />
              <input
                type="number"
                value={line.quantity}
                onChange={(e) => updateLine(idx, "quantity", parseInt(e.target.value) || 0)}
                className={`${s.input} ${s.inputSmall}`}
                min="1"
              />
              <input
                type="number"
                value={line.unit_price}
                onChange={(e) => updateLine(idx, "unit_price", e.target.value)}
                className={`${s.input} ${s.inputSmall}`}
                placeholder="0.00"
                min="0"
                step="0.01"
              />
              <div className={s.serviceLineTotal}>
                {formatAmount(lineTotal(line))}
              </div>
              <button
                type="button"
                onClick={() => removeLine(idx)}
                className={s.removeLineBtn}
                disabled={serviceLines.length <= 1}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          ))}

          <button type="button" onClick={addLine} className={s.addLineBtn}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Service Line
          </button>

          {grandTotal > 0 && (
            <div className={s.serviceTotalRow}>
              <span className={s.serviceTotalLabel}>Total:</span>
              <span className={s.serviceTotalValue}>{formatAmount(grandTotal)}</span>
            </div>
          )}
        </div>

        {/* ── Bank Details ──────────────────────── */}
        <hr className={s.sectionDivider} />
        <h4 className={s.sectionTitle}>Bank Details</h4>
        <p className={s.sectionSubtitle}>Where should reimbursement be paid?</p>

        <div className={s.formGrid}>
          <label className={`${s.label} ${s.labelRequired}`}>
            Bank Name
            <select
              value={bankName}
              onChange={(e) => { setBankName(e.target.value); setAccountName(""); }}
              className={s.select}
              required
            >
              <option value="">Select your bank...</option>
              {banks.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </label>

          <label className={`${s.label} ${s.labelRequired}`}>
            Account Number
            <input
              type="text"
              value={accountNumber}
              onChange={(e) => {
                const v = e.target.value.replace(/\D/g, "").slice(0, 10);
                setAccountNumber(v);
                if (v.length < 10) setAccountName("");
              }}
              className={s.input}
              placeholder="10-digit account number"
              maxLength={10}
              required
            />
          </label>

          <label className={`${s.label} ${s.fullWidth}`}>
            Account Name
            {bankValidating && <span style={{ color: "#888", fontWeight: 400 }}> — verifying...</span>}
            <input
              type="text"
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              className={s.input}
              placeholder={bankValidating ? "Looking up account..." : "Account holder name"}
              readOnly={bankValidating}
              required
            />
          </label>
        </div>

        {/* ── Document Upload ────────────────────── */}
        <hr className={s.sectionDivider} />
        <h4 className={s.sectionTitle}>Supporting Documents</h4>
        <p className={s.sectionSubtitle}>
          Upload receipts and medical reports. Files will be sent to the claims team via email.
        </p>

        {/* Receipts */}
        <label className={`${s.label} ${s.labelRequired}`} style={{ marginBottom: "0.5rem" }}>
          Receipts / Invoices
        </label>
        <div
          className={s.uploadZone}
          onClick={() => receiptRef.current?.click()}
        >
          <div className={s.uploadIcon}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className={s.uploadText}>Click to upload receipts</div>
          <div className={s.uploadHint}>PDF, JPG, PNG — max 5MB each</div>
          <input
            ref={receiptRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleReceiptFiles}
            style={{ display: "none" }}
          />
        </div>
        {receipts.length > 0 && (
          <div className={s.fileList}>
            {receipts.map((f, i) => (
              <div key={i} className={s.fileItem}>
                <div>
                  <span className={s.fileName}>{f.name}</span>
                  <span className={s.fileSize}>{formatFileSize(f.size)}</span>
                </div>
                <button
                  type="button"
                  className={s.fileRemoveBtn}
                  onClick={() => setReceipts((prev) => prev.filter((_, j) => j !== i))}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Medical Report */}
        <label
          className={`${s.label} ${isSecondaryCare ? s.labelRequired : ""}`}
          style={{ marginTop: "1.25rem", marginBottom: "0.5rem" }}
        >
          Medical Report
          {isSecondaryCare && (
            <span style={{ color: "#C61531", fontWeight: 400, fontSize: "0.78rem" }}>
              {" "}(required for {codeData.visit_type})
            </span>
          )}
        </label>
        <div
          className={s.uploadZone}
          onClick={() => reportRef.current?.click()}
        >
          <div className={s.uploadIcon}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#aaa" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <div className={s.uploadText}>Click to upload medical report</div>
          <div className={s.uploadHint}>PDF, JPG, PNG — max 5MB each</div>
          <input
            ref={reportRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleReportFiles}
            style={{ display: "none" }}
          />
        </div>
        {medicalReport.length > 0 && (
          <div className={s.fileList}>
            {medicalReport.map((f, i) => (
              <div key={i} className={s.fileItem}>
                <div>
                  <span className={s.fileName}>{f.name}</span>
                  <span className={s.fileSize}>{formatFileSize(f.size)}</span>
                </div>
                <button
                  type="button"
                  className={s.fileRemoveBtn}
                  onClick={() => setMedicalReport((prev) => prev.filter((_, j) => j !== i))}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        <div className={s.info} style={{ marginTop: "1rem" }}>
          Documents will be sent directly to the claims team via email.
          No files are stored on our servers.
        </div>

        {/* ── Submit ────────────────────────────── */}
        <hr className={s.sectionDivider} />
        <div className={s.btnRow}>
          <button type="button" onClick={onBack} className={s.secondaryBtn}>
            Back
          </button>
          <button type="submit" disabled={loading} className={s.primaryBtn} style={{ flex: 1 }}>
            {loading ? (
              <>
                <span className={s.spinner} />
                Submitting Claim...
              </>
            ) : (
              "Submit Reimbursement Claim"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
