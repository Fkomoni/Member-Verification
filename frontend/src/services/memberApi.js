/**
 * Member Portal API — public endpoints, no auth token required.
 */
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const memberApi = axios.create({ baseURL: API_BASE });

// ── Member Validation ────────────────────────────
export const validateMember = (enrollee_id) =>
  memberApi.post("/reimbursement/validate-member", { enrollee_id });

// ── Authorization Code ───────────────────────────
export const validateAuthCode = (code, enrollee_id) =>
  memberApi.post("/authorization/validate", { code, enrollee_id });

// ── Bank ─────────────────────────────────────────
export const getBankList = () => memberApi.get("/reimbursement/banks");

export const validateBank = (bank_name, account_number) =>
  memberApi.post("/reimbursement/validate-bank", { bank_name, account_number });

// ── Claim Submission (multipart with files) ──────
export const submitReimbursement = (formData, receiptFiles, reportFiles) => {
  const fd = new FormData();
  fd.append("data", JSON.stringify(formData));

  (receiptFiles || []).forEach((file) => {
    fd.append("receipts", file);
  });

  (reportFiles || []).forEach((file) => {
    fd.append("medical_reports", file);
  });

  return memberApi.post("/reimbursement/submit", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export default memberApi;
