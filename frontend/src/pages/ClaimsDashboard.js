import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import styles from "./DashboardPage.module.css";
import sharedStyles from "../components/shared.module.css";

export default function ClaimsDashboard() {
  const navigate = useNavigate();
  const [officer, setOfficer] = useState(() => {
    const s = localStorage.getItem("claims_officer");
    return s ? JSON.parse(s) : null;
  });
  const [claims, setClaims] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("PENDING");
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("claims_officer");
    navigate("/claims/login");
  };

  const fetchClaims = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/claims/list?status_filter=${filter}&skip=0&limit=50`);
      setClaims(data.claims || []);
      setTotal(data.total || 0);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => {
    if (!officer) { navigate("/claims/login"); return; }
    fetchClaims();
  }, [officer, navigate, fetchClaims]);

  const handleReview = async (action) => {
    if (!selectedClaim) return;
    setReviewing(true);
    try {
      await api.post(`/claims/${selectedClaim.claim_id}/review`, {
        action,
        reviewer_notes: reviewNotes,
      });
      setSelectedClaim(null);
      setReviewNotes("");
      fetchClaims();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to review claim");
    } finally { setReviewing(false); }
  };

  const formatDate = (d) => d ? d.split("T")[0] : "N/A";
  const statusColor = { PENDING: "#8B6914", APPROVED: "#0A7C3E", REJECTED: "#C61531" };
  const statusBg = { PENDING: "#FFF8E6", APPROVED: "#E8F8EE", REJECTED: "#FFF0F0" };

  if (!officer) return null;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerLogo}>
            <svg viewBox="0 0 40 40" width="32" height="32">
              <circle cx="20" cy="20" r="18" fill="url(#hdrGrad4)" />
              <defs><linearGradient id="hdrGrad4" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#F15A24" /><stop offset="100%" stopColor="#FFCE07" /></linearGradient></defs>
            </svg>
            <div>
              <span className={styles.headerBrand}>LEADWAY</span>
              <span className={styles.headerBrandHealth}> Health</span>
            </div>
          </div>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Claims Review</span>
        </div>
        <div className={styles.headerRight}>
          <div style={{ textAlign: "right" }}>
            <span className={styles.providerName}>{officer.agent_name}</span>
            <div style={{ fontSize: "0.72rem", color: "#C61531", fontWeight: 700 }}>CLAIMS OFFICER</div>
          </div>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <main className={styles.main} style={{ maxWidth: 1000 }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#263626", marginBottom: "0.25rem" }}>Reimbursement Claims</h1>
        <p style={{ color: "#777", fontSize: "0.85rem", marginBottom: "1.25rem" }}>Review and process member reimbursement claims</p>

        {/* Detail Modal */}
        {selectedClaim && (
          <div className={sharedStyles.card} style={{ marginBottom: "1.5rem", border: "2px solid #C61531" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <h2 className={sharedStyles.cardTitle}>Claim Details</h2>
              <button onClick={() => setSelectedClaim(null)} style={{ background: "none", border: "none", fontSize: "1.2rem", cursor: "pointer", color: "#888" }}>&times;</button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.85rem 1.5rem", marginBottom: "1.25rem" }}>
              <Chip label="Enrollee Name" value={selectedClaim.enrollee_name} />
              <Chip label="Enrollee ID" value={selectedClaim.enrollee_id} />
              <Chip label="PA Code" value={selectedClaim.pa_code} color="#C61531" />
              <Chip label="Visit Type" value={selectedClaim.visit_type_name} />
              <Chip label="Visit Date" value={formatDate(selectedClaim.visit_date)} />
              <Chip label="Provider" value={selectedClaim.provider_name} />
              <Chip label="Approved Amount" value={`NGN ${selectedClaim.approved_amount?.toLocaleString()}`} color="#0A7C3E" />
              <Chip label="Claim Amount" value={`NGN ${selectedClaim.claim_amount?.toLocaleString()}`} bold />
              <Chip label="Documents" value={`${selectedClaim.documents_count} file(s)`} />
              <Chip label="Bank" value={selectedClaim.bank_name} />
              <Chip label="Account No" value={selectedClaim.account_number} />
              <Chip label="Account Name" value={selectedClaim.account_name} />
            </div>

            {selectedClaim.reimbursement_reason && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={miniLabel}>Reimbursement Reason</span>
                <div style={{ fontSize: "0.9rem", color: "#444" }}>{selectedClaim.reimbursement_reason}</div>
              </div>
            )}
            <div style={{ marginBottom: "0.75rem" }}>
              <span style={miniLabel}>Reason for Visit</span>
              <div style={{ fontSize: "0.9rem", color: "#444", background: "#F8F9FA", padding: "0.6rem", borderRadius: 6 }}>{selectedClaim.reason_for_visit}</div>
            </div>
            {selectedClaim.remarks && (
              <div style={{ marginBottom: "0.75rem" }}>
                <span style={miniLabel}>Member Remarks</span>
                <div style={{ fontSize: "0.9rem", color: "#444", background: "#F8F9FA", padding: "0.6rem", borderRadius: 6 }}>{selectedClaim.remarks}</div>
              </div>
            )}

            {selectedClaim.claim_status === "PENDING" ? (
              <div style={{ borderTop: "1px solid #eee", paddingTop: "1rem", marginTop: "0.5rem" }}>
                <label className={sharedStyles.label}>
                  Review Notes
                  <textarea value={reviewNotes} onChange={(e) => setReviewNotes(e.target.value)} placeholder="Add notes for this decision (optional)" className={sharedStyles.input} style={{ marginTop: "0.25rem", minHeight: 60, resize: "vertical" }} />
                </label>
                <div style={{ display: "flex", gap: "0.75rem" }}>
                  <button onClick={() => handleReview("APPROVED")} disabled={reviewing} style={{ flex: 1, padding: "0.7rem", background: "#0A7C3E", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: "0.95rem", cursor: "pointer" }}>
                    {reviewing ? "..." : "Approve Claim"}
                  </button>
                  <button onClick={() => handleReview("REJECTED")} disabled={reviewing} style={{ flex: 1, padding: "0.7rem", background: "#C61531", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: "0.95rem", cursor: "pointer" }}>
                    {reviewing ? "..." : "Reject Claim"}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ background: statusBg[selectedClaim.claim_status], padding: "0.75rem 1rem", borderRadius: 8, marginTop: "0.5rem" }}>
                <span style={{ fontWeight: 700, color: statusColor[selectedClaim.claim_status] }}>{selectedClaim.claim_status}</span>
                {selectedClaim.reviewed_by && <span style={{ fontSize: "0.82rem", color: "#666" }}> by {selectedClaim.reviewed_by} on {formatDate(selectedClaim.reviewed_at)}</span>}
                {selectedClaim.reviewer_notes && <div style={{ fontSize: "0.85rem", color: "#444", marginTop: "0.25rem" }}>{selectedClaim.reviewer_notes}</div>}
              </div>
            )}
          </div>
        )}

        {/* Filter tabs + Claims table */}
        <div className={sharedStyles.card}>
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            {["PENDING", "APPROVED", "REJECTED", "ALL"].map((f) => (
              <button key={f} onClick={() => setFilter(f)} style={{
                padding: "0.4rem 1rem", borderRadius: 20, border: filter === f ? "2px solid #C61531" : "1.5px solid #ddd",
                background: filter === f ? "#FFF0F0" : "#fff", color: filter === f ? "#C61531" : "#666",
                fontWeight: 600, fontSize: "0.82rem", cursor: "pointer",
              }}>
                {f} {f === filter && total > 0 ? `(${total})` : ""}
              </button>
            ))}
            <button onClick={fetchClaims} disabled={loading} className={sharedStyles.secondaryBtn} style={{ marginTop: 0, marginLeft: "auto", padding: "0.35rem 0.8rem", fontSize: "0.78rem" }}>
              {loading ? "..." : "Refresh"}
            </button>
          </div>

          {claims.length === 0 ? (
            <p style={{ color: "#999", textAlign: "center", padding: "2rem 0" }}>No {filter !== "ALL" ? filter.toLowerCase() : ""} claims found</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #eee" }}>
                    <th style={th}>Date</th>
                    <th style={th}>Enrollee</th>
                    <th style={th}>PA Code</th>
                    <th style={th}>Visit Type</th>
                    <th style={th}>Provider</th>
                    <th style={th}>Amount</th>
                    <th style={th}>Status</th>
                    <th style={th}></th>
                  </tr>
                </thead>
                <tbody>
                  {claims.map((c) => (
                    <tr key={c.claim_id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={td}>{formatDate(c.created_at)}</td>
                      <td style={td}>
                        <div style={{ fontWeight: 600 }}>{c.enrollee_name}</div>
                        <div style={{ fontSize: "0.72rem", color: "#999" }}>{c.enrollee_id}</div>
                      </td>
                      <td style={td}><code style={{ fontWeight: 700, color: "#C61531" }}>{c.pa_code}</code></td>
                      <td style={td}>{c.visit_type_name}</td>
                      <td style={td}>{c.provider_name}</td>
                      <td style={td}>
                        <div style={{ fontWeight: 700 }}>NGN {c.claim_amount?.toLocaleString()}</div>
                        <div style={{ fontSize: "0.72rem", color: "#888" }}>of {c.approved_amount?.toLocaleString()}</div>
                      </td>
                      <td style={td}>
                        <span style={{ padding: "0.15rem 0.5rem", borderRadius: 12, fontSize: "0.72rem", fontWeight: 700, background: statusBg[c.claim_status], color: statusColor[c.claim_status] }}>
                          {c.claim_status}
                        </span>
                      </td>
                      <td style={td}>
                        <button onClick={() => { setSelectedClaim(c); setReviewNotes(""); }} style={{ background: "none", border: "1.5px solid #C61531", color: "#C61531", padding: "0.25rem 0.6rem", borderRadius: 6, fontWeight: 600, fontSize: "0.75rem", cursor: "pointer" }}>
                          View
                        </button>
                      </td>
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

const miniLabel = { fontSize: "0.7rem", color: "#999", textTransform: "uppercase", fontWeight: 600, display: "block", marginBottom: "0.15rem" };
const th = { textAlign: "left", padding: "0.6rem 0.5rem", color: "#888", fontWeight: 600, fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.04em" };
const td = { padding: "0.65rem 0.5rem", verticalAlign: "top" };

function Chip({ label, value, color, bold }) {
  return (
    <div>
      <span style={miniLabel}>{label}</span>
      <div style={{ fontWeight: bold ? 800 : 700, fontSize: "0.9rem", color: color || "#263626" }}>{value}</div>
    </div>
  );
}
