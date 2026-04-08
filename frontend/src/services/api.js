import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_BASE });

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────
export const login = (email, password) =>
  api.post("/login", { email, password });

// ── Members ───────────────────────────────────────
export const verifyMember = (enrolleeId) =>
  api.post("/verify-member", { enrollee_id: enrolleeId });

// ── Biometrics ────────────────────────────────────
export const captureBiometric = (memberId, templateB64, fingerPosition, nin, lfdPassed, imageQuality) =>
  api.post("/capture-biometric", {
    member_id: memberId,
    fingerprint_template_b64: templateB64,
    finger_position: fingerPosition || "right_thumb",
    nin: nin || null,
    lfd_passed: lfdPassed ?? true,
    image_quality: imageQuality ?? 0,
  });

export const validateFingerprint = (memberId, templateB64, lfdPassed, imageQuality) =>
  api.post("/validate-fingerprint", {
    member_id: memberId,
    fingerprint_template_b64: templateB64,
    lfd_passed: lfdPassed ?? true,
    image_quality: imageQuality ?? 0,
  });

// ── Service / Visit Types ────────────────────────
export const getServiceTypes = (cifNumber, schemeId) =>
  api.post("/service-types", { cif_number: cifNumber, scheme_id: schemeId });

// ── Visits / Claims ──────────────────────────────
export const logVisit = (memberId, providerId, verificationToken) =>
  api.post("/log-visit", {
    member_id: memberId,
    provider_id: providerId,
    verification_token: verificationToken,
  });

export const validateClaim = (verificationToken, timestamp, providerId) =>
  api.post("/validate-claim", {
    verification_token: verificationToken,
    timestamp,
    provider_id: providerId,
  });

// ── Claims Status ────────────────────────────────
export const getClaimsStatus = (enrolleeId) =>
  api.post("/claims-status", { enrollee_id: enrolleeId });

export default api;
