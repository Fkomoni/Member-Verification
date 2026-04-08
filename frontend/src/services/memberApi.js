/**
 * Member Portal API — public endpoints, no auth token required.
 */
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const memberApi = axios.create({ baseURL: API_BASE });

// ── Member Validation ────────────────────────────
export const validateMember = (enrollee_id, phone) =>
  memberApi.post("/reimbursement/validate-member", { enrollee_id, phone });

// ── Authorization Code ───────────────────────────
export const validateAuthCode = (code, enrollee_id) =>
  memberApi.post("/authorization/validate", { code, enrollee_id });

// ── Bank ─────────────────────────────────────────
export const getBankList = () => memberApi.get("/reimbursement/banks");

export const validateBank = (bank_name, account_number) =>
  memberApi.post("/reimbursement/validate-bank", { bank_name, account_number });

// ── Claim Submission ─────────────────────────────
export const submitReimbursement = (data) =>
  memberApi.post("/reimbursement/submit", data);

export default memberApi;
