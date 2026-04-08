import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import styles from "./DashboardPage.module.css";
import sharedStyles from "../components/shared.module.css";

export default function CallCenterDashboard() {
  const navigate = useNavigate();
  const [agent, setAgent] = useState(() => {
    const s = localStorage.getItem("agent");
    return s ? JSON.parse(s) : null;
  });

  // Lookup state
  const [enrolleeId, setEnrolleeId] = useState("");
  const [member, setMember] = useState(null);
  const [lookupError, setLookupError] = useState("");
  const [lookupLoading, setLookupLoading] = useState(false);

  // Visit types
  const [visitTypes, setVisitTypes] = useState([]);
  const [selectedVisitType, setSelectedVisitType] = useState(null);

  // PA form
  const [approvedAmount, setApprovedAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState(null);

  // Code history
  const [codes, setCodes] = useState([]);
  const [codesLoading, setCodesLoading] = useState(false);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("agent");
    navigate("/call-center/login");
  };

  const fetchCodes = useCallback(async () => {
    setCodesLoading(true);
    try {
      const { data } = await api.get("/authorization/codes?skip=0&limit=50");
      setCodes(data);
    } catch {
      // ignore
    } finally {
      setCodesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!agent) {
      navigate("/call-center/login");
      return;
    }
    fetchCodes();
  }, [agent, navigate, fetchCodes]);

  const handleLookup = async (e) => {
    e.preventDefault();
    setLookupError("");
    setMember(null);
    setVisitTypes([]);
    setSelectedVisitType(null);
    setGeneratedCode(null);
    setLookupLoading(true);
    try {
      const { data } = await api.get(`/authorization/lookup-member?enrollee_id=${encodeURIComponent(enrolleeId.trim())}`);
      setMember(data);
      // Fetch visit types
      if (data.cif_number && data.scheme_id) {
        try {
          const vt = await api.get(`/authorization/visit-types?cif=${data.cif_number}&scheme_id=${data.scheme_id}`);
          setVisitTypes(vt.data.service_types || []);
        } catch {
          // visit types optional
        }
      }
    } catch (err) {
      setLookupError(err.response?.data?.detail || "Not Found");
    } finally {
      setLookupLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!member || !selectedVisitType) return;
    setGenerating(true);
    try {
      const { data } = await api.post("/authorization/generate", {
        enrollee_id: member.enrollee_id,
        enrollee_name: member.name,
        visit_type_id: selectedVisitType.servtype_id,
        visit_type_name: selectedVisitType.visittype,
        approved_amount: parseFloat(approvedAmount) || 0,
        cif_number: member.cif_number || "",
        scheme_id: member.scheme_id || "",
        notes,
      });
      setGeneratedCode(data);
      setApprovedAmount("");
      setNotes("");
      setSelectedVisitType(null);
      fetchCodes();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to generate code");
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (d) => {
    if (!d) return "N/A";
    return d.split("T")[0];
  };

  if (!agent) return null;

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerLogo}>
            <svg viewBox="0 0 40 40" width="32" height="32">
              <circle cx="20" cy="20" r="18" fill="url(#hdrGrad2)" />
              <defs>
                <linearGradient id="hdrGrad2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#F15A24" />
                  <stop offset="100%" stopColor="#FFCE07" />
                </linearGradient>
              </defs>
            </svg>
            <div>
              <span className={styles.headerBrand}>LEADWAY</span>
              <span className={styles.headerBrandHealth}> Health</span>
            </div>
          </div>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Call Center Portal</span>
        </div>
        <div className={styles.headerRight}>
          <div style={{ textAlign: "right" }}>
            <span className={styles.providerName}>{agent.agent_name}</span>
            <div style={{ fontSize: "0.72rem", color: "#C61531", fontWeight: 700 }}>CALL CENTER AGENT</div>
          </div>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <main className={styles.main} style={{ maxWidth: 900 }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#263626", marginBottom: "0.25rem" }}>
          Authorization Code Management
        </h1>
        <p style={{ color: "#777", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
          Generate and manage authorization codes for member reimbursement claims
        </p>

        {/* Generate PA Code Card */}
        <div className={sharedStyles.card} style={{ marginBottom: "1.5rem" }}>
          <h2 className={sharedStyles.cardTitle}>Generate Authorization Code</h2>
          <p className={sharedStyles.cardSubtitle}>Create a new authorization code for a member's reimbursement claim</p>

          {/* Enrollee Lookup */}
          <label className={sharedStyles.label}>
            Enrollee ID *
            <form onSubmit={handleLookup} className={sharedStyles.row} style={{ marginTop: "0.25rem" }}>
              <input
                type="text"
                placeholder="21000645/0"
                value={enrolleeId}
                onChange={(e) => setEnrolleeId(e.target.value)}
                required
                className={sharedStyles.input}
              />
              <button type="submit" disabled={lookupLoading} className={sharedStyles.primaryBtn}>
                {lookupLoading ? "Looking up..." : "Look Up"}
              </button>
            </form>
          </label>

          {lookupError && <div className={sharedStyles.error}>{lookupError}</div>}

          {/* Member Verified Banner */}
          {member && (
            <div style={{
              background: "#E8F8EE", border: "1.5px solid #B5E8C9", borderRadius: 10,
              padding: "1rem 1.25rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.75rem"
            }}>
              <span style={{ fontSize: "1.5rem" }}>&#10004;</span>
              <div style={{ flex: 1 }}>
                <div style={{ color: "#0A7C3E", fontWeight: 700, fontSize: "0.95rem", marginBottom: "0.25rem" }}>
                  Member Verified
                </div>
                <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
                  <div>
                    <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Full Name</span>
                    <div style={{ fontWeight: 700, fontSize: "0.92rem", color: "#263626" }}>{member.name}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Enrollee ID</span>
                    <div style={{ fontWeight: 700, fontSize: "0.92rem", color: "#263626" }}>{member.enrollee_id}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Plan</span>
                    <div style={{ fontWeight: 700, fontSize: "0.92rem", color: "#263626" }}>{member.plan || "N/A"}</div>
                  </div>
                  <div>
                    <span style={{ fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600 }}>Status</span>
                    <div style={{ fontWeight: 700, fontSize: "0.92rem", color: member.member_status === "Active" ? "#0A7C3E" : "#C61531" }}>
                      {member.member_status || "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* PA Form (only shown when member found) */}
          {member && (
            <>
              <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
                <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                  Approved Amount (NGN) *
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0.00"
                    value={approvedAmount}
                    onChange={(e) => setApprovedAmount(e.target.value)}
                    className={sharedStyles.input}
                    style={{ marginTop: "0.25rem" }}
                  />
                </label>
                <label className={sharedStyles.label} style={{ flex: 1, minWidth: 200 }}>
                  Visit Type *
                  <select
                    value={selectedVisitType ? selectedVisitType.servtype_id : ""}
                    onChange={(e) => {
                      const vt = visitTypes.find(v => String(v.servtype_id) === e.target.value);
                      setSelectedVisitType(vt || null);
                    }}
                    className={sharedStyles.input}
                    style={{ marginTop: "0.25rem" }}
                  >
                    <option value="">Select visit type...</option>
                    {visitTypes.map((vt) => (
                      <option key={vt.servtype_id} value={vt.servtype_id}>
                        {vt.visittype}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label className={sharedStyles.label}>
                Notes
                <textarea
                  placeholder="Additional notes about this authorization (optional)"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className={sharedStyles.input}
                  style={{ marginTop: "0.25rem", minHeight: 80, resize: "vertical" }}
                />
              </label>

              <button
                onClick={handleGenerate}
                disabled={generating || !selectedVisitType}
                className={sharedStyles.primaryBtn}
                style={{ marginTop: "0.5rem" }}
              >
                {generating ? "Generating..." : "Generate Authorization Code"}
              </button>
            </>
          )}

          {/* Generated Code Result */}
          {generatedCode && (
            <div style={{
              background: "#E8F8EE", border: "2px solid #0A7C3E", borderRadius: 10,
              padding: "1.25rem", marginTop: "1.25rem", textAlign: "center"
            }}>
              <div style={{ fontSize: "0.8rem", color: "#0A7C3E", fontWeight: 600, marginBottom: "0.5rem" }}>
                Authorization Code Generated
              </div>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#0A7C3E", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
                {generatedCode.code}
              </div>
              <div style={{ fontSize: "0.82rem", color: "#666" }}>
                {generatedCode.enrollee_name} &mdash; {generatedCode.visit_type_name}
                {generatedCode.approved_amount > 0 && ` &mdash; NGN ${generatedCode.approved_amount.toLocaleString()}`}
              </div>
              <div style={{ fontSize: "0.75rem", color: "#999", marginTop: "0.25rem" }}>
                Expires: {formatDate(generatedCode.expires_at)}
              </div>
            </div>
          )}
        </div>

        {/* Code History */}
        <div className={sharedStyles.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <div>
              <h2 className={sharedStyles.cardTitle}>Authorization Code History</h2>
              <p className={sharedStyles.cardSubtitle} style={{ marginBottom: 0 }}>
                {codes.length} code{codes.length !== 1 ? "s" : ""} generated
              </p>
            </div>
            <button onClick={fetchCodes} disabled={codesLoading} className={sharedStyles.secondaryBtn} style={{ marginTop: 0, padding: "0.4rem 0.8rem", fontSize: "0.8rem" }}>
              {codesLoading ? "..." : "Refresh"}
            </button>
          </div>

          {codes.length === 0 ? (
            <p style={{ color: "#999", fontSize: "0.85rem", textAlign: "center", padding: "2rem 0" }}>
              No authorization codes generated yet
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #eee" }}>
                    <th style={thStyle}>Code</th>
                    <th style={thStyle}>Enrollee</th>
                    <th style={thStyle}>Visit Type</th>
                    <th style={thStyle}>Amount</th>
                    <th style={thStyle}>Status</th>
                    <th style={thStyle}>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {codes.map((c) => (
                    <tr key={c.code_id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={tdStyle}><code style={{ fontWeight: 700, color: "#C61531" }}>{c.code}</code></td>
                      <td style={tdStyle}>
                        <div style={{ fontWeight: 600 }}>{c.enrollee_name}</div>
                        <div style={{ fontSize: "0.75rem", color: "#999" }}>{c.enrollee_id}</div>
                      </td>
                      <td style={tdStyle}>{c.visit_type_name}</td>
                      <td style={tdStyle}>{c.approved_amount > 0 ? `NGN ${c.approved_amount.toLocaleString()}` : "-"}</td>
                      <td style={tdStyle}>
                        <span style={{
                          padding: "0.15rem 0.5rem", borderRadius: 12, fontSize: "0.72rem", fontWeight: 700,
                          background: c.status === "ACTIVE" ? "#E8F8EE" : "#F8F9FA",
                          color: c.status === "ACTIVE" ? "#0A7C3E" : "#888",
                        }}>
                          {c.status}
                        </span>
                      </td>
                      <td style={tdStyle}>{formatDate(c.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

const thStyle = { textAlign: "left", padding: "0.6rem 0.5rem", color: "#888", fontWeight: 600, fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.04em" };
const tdStyle = { padding: "0.65rem 0.5rem", verticalAlign: "top" };
