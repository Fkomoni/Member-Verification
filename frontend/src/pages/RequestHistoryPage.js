import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { listMedicationRequests } from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./RequestHistoryPage.module.css";

const STATUS_LABELS = {
  submitted: "Submitted",
  under_review: "Under Review",
  routed_wellahealth: "Routed → WellaHealth",
  sent_whatsapp_lagos: "Sent → WhatsApp (Lagos)",
  sent_whatsapp_outside_lagos: "Sent → WhatsApp (Outside Lagos)",
  awaiting_fulfilment: "Awaiting Fulfilment",
  in_progress: "In Progress",
  completed: "Completed",
  failed: "Failed",
  escalated: "Escalated",
  cancelled: "Cancelled",
};

const CLASS_LABELS = {
  acute: "Acute",
  chronic: "Chronic",
  mixed: "Mixed",
  review_required: "Review",
};

export default function RequestHistoryPage() {
  const { provider, logout } = useAuth();
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const perPage = 15;

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await listMedicationRequests(page, perPage, statusFilter || undefined);
      setRequests(data.requests);
      setTotal(data.total);
    } catch (err) {
      setError("Failed to load requests");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  const totalPages = Math.ceil(total / perPage);

  const fmtDate = (iso) => {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-NG", { day: "2-digit", month: "short", year: "numeric" }) +
      " " + d.toLocaleTimeString("en-NG", { hour: "2-digit", minute: "2-digit" });
  };

  const statusBadgeClass = (s) => {
    if (s === "completed") return styles.badgeSuccess;
    if (s === "failed" || s === "escalated" || s === "cancelled") return styles.badgeDanger;
    if (s === "under_review") return styles.badgeWarning;
    if (s?.startsWith("routed") || s?.startsWith("sent")) return styles.badgeInfo;
    return styles.badgeDefault;
  };

  const classBadgeClass = (c) => {
    if (c === "acute") return styles.clsAcute;
    if (c === "chronic") return styles.clsChronic;
    if (c === "mixed") return styles.clsMixed;
    return styles.clsReview;
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.headerLogo}>
            <img src={logo} alt="Leadway Health" className={styles.headerLogoImg} />
          </Link>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Rx Routing Hub</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.providerName}>{provider?.provider_name}</span>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <nav className={styles.navBar}>
        
        <Link to="/medication-request" className={styles.navLink}>New Rx Request</Link>
        <Link to="/medication-requests" className={styles.navLinkActive}>Request History</Link>
      </nav>

      <main className={styles.main}>
        <div className={styles.titleRow}>
          <div>
            <h1 className={styles.pageTitle}>Request History</h1>
            <p className={styles.pageSubtitle}>{total} total request{total !== 1 ? "s" : ""}</p>
          </div>
          <div className={styles.filters}>
            <select
              className={styles.filterSelect}
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            >
              <option value="">All Statuses</option>
              {Object.entries(STATUS_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
            <Link to="/medication-request" className={styles.newReqBtn}>+ New Request</Link>
          </div>
        </div>

        {error && <div className={styles.errorBanner}>{error}</div>}

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Enrollee</th>
                <th>Medications</th>
                <th>Type</th>
                <th>Route</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className={styles.emptyCell}>Loading...</td></tr>
              ) : requests.length === 0 ? (
                <tr><td colSpan={7} className={styles.emptyCell}>No requests found</td></tr>
              ) : requests.map((r) => (
                <tr key={r.request_id}>
                  <td className={styles.refCell}>{r.reference_number}</td>
                  <td>
                    <div className={styles.enrolleeName}>{r.enrollee_name}</div>
                    <div className={styles.enrolleeId}>{r.enrollee_id}</div>
                  </td>
                  <td>
                    <div className={styles.medList}>
                      {r.items.slice(0, 3).map((item, i) => (
                        <span key={i} className={styles.medPill}>{item.drug_name}</span>
                      ))}
                      {r.items.length > 3 && (
                        <span className={styles.medMore}>+{r.items.length - 3} more</span>
                      )}
                    </div>
                  </td>
                  <td>
                    {r.classification ? (
                      <span className={`${styles.clsBadge} ${classBadgeClass(r.classification.classification)}`}>
                        {CLASS_LABELS[r.classification.classification] || r.classification.classification}
                      </span>
                    ) : "—"}
                  </td>
                  <td>
                    {r.routing ? (
                      <span className={styles.routeText}>
                        {r.routing.destination === "wellahealth" ? "WellaHealth" :
                         r.routing.destination === "whatsapp_lagos" ? "WhatsApp (Lagos)" :
                         r.routing.destination === "whatsapp_outside_lagos" ? "WhatsApp (Outside)" :
                         "Review"}
                      </span>
                    ) : "—"}
                  </td>
                  <td>
                    <span className={`${styles.statusBadge} ${statusBadgeClass(r.status)}`}>
                      {STATUS_LABELS[r.status] || r.status}
                    </span>
                  </td>
                  <td className={styles.dateCell}>{fmtDate(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className={styles.pagination}>
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className={styles.pageBtn}
            >Previous</button>
            <span className={styles.pageInfo}>Page {page} of {totalPages}</span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className={styles.pageBtn}
            >Next</button>
          </div>
        )}
      </main>
    </div>
  );
}
