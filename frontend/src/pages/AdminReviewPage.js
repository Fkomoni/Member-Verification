import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getReviewQueue, overrideClassification, overrideRouting, updateRequestStatus, addAdminComment, getRequestAudit } from "../services/adminApi";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./AdminReviewPage.module.css";

export default function AdminReviewPage() {
  const { provider, logout } = useAuth();
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [queueType, setQueueType] = useState("all");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [audit, setAudit] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [comment, setComment] = useState("");

  const perPage = 15;

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await getReviewQueue(page, perPage, queueType);
      setRequests(data.requests);
      setTotal(data.total);
    } catch { /* ignore */ }
    setLoading(false);
  }, [page, queueType]);

  useEffect(() => { fetchQueue(); }, [fetchQueue]);

  const selectRequest = async (req) => {
    setSelected(req);
    try {
      const { data } = await getRequestAudit(req.request_id);
      setAudit(data);
    } catch { setAudit([]); }
  };

  const doOverrideClassification = async (cls) => {
    if (!selected) return;
    setActionLoading(true);
    try {
      await overrideClassification(selected.request_id, cls, `Admin override to ${cls}`);
      await fetchQueue();
      setSelected(null);
    } catch { /* ignore */ }
    setActionLoading(false);
  };

  const doOverrideRouting = async (dest) => {
    if (!selected) return;
    setActionLoading(true);
    try {
      await overrideRouting(selected.request_id, dest, `Admin routed to ${dest}`);
      await fetchQueue();
      setSelected(null);
    } catch { /* ignore */ }
    setActionLoading(false);
  };

  const doUpdateStatus = async (newStatus) => {
    if (!selected) return;
    setActionLoading(true);
    try {
      await updateRequestStatus(selected.request_id, newStatus, `Admin set ${newStatus}`);
      await fetchQueue();
      setSelected(null);
    } catch { /* ignore */ }
    setActionLoading(false);
  };

  const doAddComment = async () => {
    if (!selected || !comment.trim()) return;
    setActionLoading(true);
    try {
      await addAdminComment(selected.request_id, comment.trim());
      setComment("");
      const { data } = await getRequestAudit(selected.request_id);
      setAudit(data);
    } catch { /* ignore */ }
    setActionLoading(false);
  };

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.headerLogo}>
            <img src={logo} alt="Leadway Health" className={styles.headerLogoImg} />
          </Link>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Admin Review</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.providerName}>{provider?.provider_name}</span>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <nav className={styles.navBar}>
        <Link to="/medication-request" className={styles.navLink}>New Rx Request</Link>
        <Link to="/medication-requests" className={styles.navLink}>Request History</Link>
        <Link to="/admin/review" className={styles.navLinkActive}>Review Queue</Link>
        <Link to="/reports" className={styles.navLink}>Reports</Link>
      </nav>

      <main className={styles.main}>
        <div className={styles.layout}>
          {/* Left: Queue list */}
          <div className={styles.queuePanel}>
            <div className={styles.queueHeader}>
              <h2 className={styles.queueTitle}>Review Queue ({total})</h2>
              <select className={styles.filterSelect} value={queueType} onChange={(e) => { setQueueType(e.target.value); setPage(1); }}>
                <option value="all">All Pending</option>
                <option value="review">Under Review</option>
                <option value="failed">Failed</option>
                <option value="pending">Submitted</option>
              </select>
            </div>

            {loading ? <div className={styles.emptyState}>Loading...</div> :
             requests.length === 0 ? <div className={styles.emptyState}>No requests in queue</div> :
             requests.map((r) => (
              <div
                key={r.request_id}
                className={`${styles.queueItem} ${selected?.request_id === r.request_id ? styles.queueItemActive : ""}`}
                onClick={() => selectRequest(r)}
              >
                <div className={styles.queueItemRef}>{r.reference_number}</div>
                <div className={styles.queueItemMeta}>
                  {r.enrollee_name} &middot; {r.items.length} med{r.items.length !== 1 ? "s" : ""}
                </div>
                <div className={styles.queueItemStatus}>
                  <span className={styles.statusTag}>{r.status.replace(/_/g, " ")}</span>
                  {r.classification && (
                    <span className={styles.clsTag}>{r.classification.classification}</span>
                  )}
                </div>
              </div>
            ))}

            {totalPages > 1 && (
              <div className={styles.pagination}>
                <button disabled={page <= 1} onClick={() => setPage(page - 1)} className={styles.pageBtn}>Prev</button>
                <span className={styles.pageInfo}>{page}/{totalPages}</span>
                <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className={styles.pageBtn}>Next</button>
              </div>
            )}
          </div>

          {/* Right: Detail & Actions */}
          <div className={styles.detailPanel}>
            {!selected ? (
              <div className={styles.emptyState}>Select a request to review</div>
            ) : (
              <>
                <h3 className={styles.detailTitle}>{selected.reference_number}</h3>
                <div className={styles.detailGrid}>
                  <div><span className={styles.dl}>Enrollee</span><span className={styles.dv}>{selected.enrollee_name} ({selected.enrollee_id})</span></div>
                  <div><span className={styles.dl}>Facility</span><span className={styles.dv}>{selected.facility_name}</span></div>
                  <div><span className={styles.dl}>Doctor</span><span className={styles.dv}>{selected.treating_doctor}</span></div>
                  <div><span className={styles.dl}>Location</span><span className={styles.dv}>{selected.delivery_state}, {selected.delivery_lga}</span></div>
                  <div><span className={styles.dl}>Status</span><span className={styles.dv}>{selected.status}</span></div>
                  <div><span className={styles.dl}>Classification</span><span className={styles.dv}>{selected.classification?.classification || "—"}</span></div>
                </div>

                <h4 className={styles.subTitle}>Medications</h4>
                {selected.items.map((item, i) => (
                  <div key={i} className={styles.medItem}>
                    <span className={styles.medIdx}>{i + 1}.</span>
                    <span className={styles.medName}>{item.drug_name}</span>
                    <span className={styles.medDose}>{item.dosage_instruction}, {item.duration}, Qty: {item.quantity}</span>
                    <span className={styles.medCat}>{item.item_category || "?"}</span>
                    {item.requires_review && <span className={styles.reviewFlag}>review</span>}
                  </div>
                ))}

                <h4 className={styles.subTitle}>Actions</h4>
                <div className={styles.actionRow}>
                  <span className={styles.actionLabel}>Override Classification:</span>
                  {["acute", "chronic", "mixed"].map((c) => (
                    <button key={c} className={styles.actionBtn} disabled={actionLoading} onClick={() => doOverrideClassification(c)}>{c}</button>
                  ))}
                </div>
                <div className={styles.actionRow}>
                  <span className={styles.actionLabel}>Force Route:</span>
                  {[["wellahealth", "WellaHealth"], ["whatsapp_lagos", "WA Lagos"], ["whatsapp_outside_lagos", "WA Outside"]].map(([d, l]) => (
                    <button key={d} className={styles.actionBtn} disabled={actionLoading} onClick={() => doOverrideRouting(d)}>{l}</button>
                  ))}
                </div>
                <div className={styles.actionRow}>
                  <span className={styles.actionLabel}>Status:</span>
                  {["completed", "cancelled", "escalated"].map((s) => (
                    <button key={s} className={styles.actionBtnAlt} disabled={actionLoading} onClick={() => doUpdateStatus(s)}>{s}</button>
                  ))}
                </div>

                <h4 className={styles.subTitle}>Comment</h4>
                <div className={styles.commentRow}>
                  <input className={styles.commentInput} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add internal note..." />
                  <button className={styles.commentBtn} onClick={doAddComment} disabled={actionLoading || !comment.trim()}>Add</button>
                </div>

                <h4 className={styles.subTitle}>Audit Trail</h4>
                <div className={styles.auditList}>
                  {audit.map((a, i) => (
                    <div key={i} className={styles.auditItem}>
                      <span className={styles.auditType}>{a.event_type}</span>
                      <span className={styles.auditDetail}>{a.detail}</span>
                      <span className={styles.auditTime}>{new Date(a.timestamp).toLocaleString("en-NG")}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
