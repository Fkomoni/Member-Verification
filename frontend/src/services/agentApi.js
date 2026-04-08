import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

const agentApi = axios.create({ baseURL: API_BASE });

// Attach agent JWT to every request
agentApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("agent_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Agent Auth ───────────────────────────────────
export const agentLogin = (email, password) =>
  agentApi.post("/agent/login", { email, password });

export const seedAgents = () => agentApi.post("/agent/seed");

// ── Authorization Codes ──────────────────────────
export const generateAuthCode = ({ enrollee_id, approved_amount, visit_type, notes }) =>
  agentApi.post("/authorization/generate", {
    enrollee_id,
    approved_amount,
    visit_type,
    notes: notes || null,
  });

export const validateAuthCode = (code, enrollee_id) =>
  agentApi.post("/authorization/validate", { code, enrollee_id });

export const listMyCodes = (skip = 0, limit = 50) =>
  agentApi.get("/authorization/codes", { params: { skip, limit } });

export const getCodeDetail = (code) =>
  agentApi.get(`/authorization/codes/${code}`);

export default agentApi;
