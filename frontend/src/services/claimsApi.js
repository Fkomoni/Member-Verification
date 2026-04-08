/**
 * Claims Portal API — requires agent JWT (claims_officer or admin role).
 */
import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const claimsApi = axios.create({ baseURL: API_BASE });

// Attach agent JWT
claimsApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("agent_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Claims ────────────────────────────────────────
export const listClaims = ({ status, search, skip = 0, limit = 50 } = {}) =>
  claimsApi.get("/claims-portal/claims", {
    params: { status, search, skip, limit },
  });

export const getClaimDetail = (claimId) =>
  claimsApi.get(`/claims-portal/claims/${claimId}`);

export const updateClaimStatus = (claimId, { status, approved_amount, reviewer_notes }) =>
  claimsApi.patch(`/claims-portal/claims/${claimId}/status`, {
    status,
    approved_amount: approved_amount || null,
    reviewer_notes: reviewer_notes || null,
  });

export const getClaimTimeline = (claimId) =>
  claimsApi.get(`/claims-portal/claims/${claimId}/timeline`);

// ── Stats ─────────────────────────────────────────
export const getClaimsStats = () => claimsApi.get("/claims-portal/stats");

// ── Export ────────────────────────────────────────
export const exportClaimsExcel = (statusFilter) => {
  const params = statusFilter ? `?status=${statusFilter}` : "";
  return claimsApi.get(`/claims-portal/export${params}`, {
    responseType: "blob",
  });
};

export default claimsApi;
