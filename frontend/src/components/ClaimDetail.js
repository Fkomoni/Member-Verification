import React, { useEffect, useState } from "react";
import { getClaimDetail, getClaimTimeline, updateClaimStatus } from "../services/claimsApi";
import s from "./claimsportal.module.css";

const STATUS_FLOW = [
  "submitted",
  "under_review",
  "pending_info",
  "approved",
  "rejected",
  "payment_processing",
  "paid",
];

const NEXT_ACTIONS = {
  submitted: [{ value: "under_review", label: "Start Review" }],
  under_review: [
    { value: "approved", label: "Approve" },
    { value: "rejected", label: "Reject" },
    { value: "pending_info", label: "Request More Info" },
  ],
  pending_info: [{ value: "under_review", label: "Resume Review" }],
  approved: [{ value: "payment_processing", label: "Send to Payment" }],
  payment_processing: [{ value: "paid", label: "Mark as Paid" }],
  rejected: [],
  paid: [],
};

export default function ClaimDetail({ claimId, onBack, onStatusChanged }) {
  const [claim, setClaim] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [approvedAmt, setApprovedAmt] = useState("");

  useEffect(() => {
    loadData();
  }, [claimId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [detailRes, timelineRes] = await Promise.all([
        getClaimDetail(claimId),
        getClaimTimeline(claimId),
      ]);
      setClaim(detailRes.data);
      setTimeline(timelineRes.data);
      setApprovedAmt(detailRes.data.approved_amount || "");
    } catch {
      setError("Failed to load claim details");
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    setError("");
    try {
      await updateClaimStatus(claimId, {
        status: newStatus,
        approved_amount: approvedAmt ? parseFloat(approvedAmt) : null,
        reviewer_notes: reviewNotes.trim() || null,
      });
      await loadData();
      setReviewNotes("");
      if (onStatusChanged) onStatusChanged();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update status");
    } finally {
      setUpdating(false);
    }
  };

  const fmt = (amount) =>
    amount != null
      ? new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" }).format(amount)
      : "—";

  const fmtDate = (d) =>
    new Date(d).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });

  const statusLabel = (st) => st.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  if (loading) {
    return <div className={s.card}><div className={s.loadingState}>Loading claim details...</div></div>;
  }

  if (!claim) {
    return <div className={s.card}><div className={s.emptyState}><p>Claim not found</p></div></div>;
  }

  const actions = NEXT_ACTIONS[claim.status] || [];

  return (
    <div>
      {/* Header */}
      <div className={s.detailHeader}>
        <button onClick={onBack} className={s.backBtn}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back to Claims
        </button>
        <div className={s.detailHeaderInfo}>
          <h2 className={s.detailRef}>{claim.claim_ref}</h2>
          <span className={`${s.statusBadge} ${s[{
            submitted: "statusSubmitted", under_review: "statusReview",
            pending_info: "statusPending", approved: "statusApproved",
            rejected: "statusRejected", payment_processing: "statusProcessing",
            paid: "statusPaid",
          }[claim.status]] || ""}`}>
            {statusLabel(claim.status)}
          </span>
        </div>
      </div>

      {error && <div className={s.error}>{error}</div>}

      <div className={s.detailGrid}>
        {/* Left column — Claim info */}
        <div className={s.card}>
          <h4 className={s.sectionTitle}>Member</h4>
          <div className={s.infoGrid}>
            <div><span className={s.infoLabel}>Name</span><span className={s.infoValue}>{claim.member_name}</span></div>
            <div><span className={s.infoLabel}>Enrollee ID</span><span className={s.infoValue}>{claim.enrollee_id}</span></div>
            <div><span className={s.infoLabel}>Phone</span><span className={s.infoValue}>{claim.member_phone}</span></div>
          </div>

          <h4 className={s.sectionTitle} style={{ marginTop: "1.25rem" }}>Authorization</h4>
          <div className={s.infoGrid}>
            <div><span className={s.infoLabel}>Code</span><span className={s.infoValueCode}>{claim.authorization_code}</span></div>
            <div><span className={s.infoLabel}>Agent</span><span className={s.infoValue}>{claim.agent_name || "—"}</span></div>
          </div>

          <h4 className={s.sectionTitle} style={{ marginTop: "1.25rem" }}>Claim Details</h4>
          <div className={s.infoGrid}>
            <div><span className={s.infoLabel}>Hospital</span><span className={s.infoValue}>{claim.hospital_name}</span></div>
            <div><span className={s.infoLabel}>Visit Date</span><span className={s.infoValue}>{claim.visit_date}</span></div>
            <div><span className={s.infoLabel}>Reason</span><span className={s.infoValue}>{claim.reason_for_visit}</span></div>
            <div><span className={s.infoLabel}>Reimbursement Reason</span><span className={s.infoValue}>{claim.reimbursement_reason}</span></div>
          </div>

          <div className={s.amountBar}>
            <div><span className={s.amountLabel}>Claim Amount</span><span className={s.amountValueLarge}>{fmt(claim.claim_amount)}</span></div>
            <div><span className={s.amountLabel}>Approved Amount</span><span className={s.amountValueLarge}>{fmt(claim.approved_amount)}</span></div>
          </div>

          {claim.medications && <div className={s.textBlock}><span className={s.infoLabel}>Medications</span><p>{claim.medications}</p></div>}
          {claim.lab_investigations && <div className={s.textBlock}><span className={s.infoLabel}>Lab Investigations</span><p>{claim.lab_investigations}</p></div>}
          {claim.comments && <div className={s.textBlock}><span className={s.infoLabel}>Comments</span><p>{claim.comments}</p></div>}

          {claim.service_lines?.length > 0 && (
            <>
              <h4 className={s.sectionTitle} style={{ marginTop: "1.25rem" }}>Services</h4>
              <table className={s.miniTable}>
                <thead><tr><th>Service</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
                <tbody>
                  {claim.service_lines.map((sl, i) => (
                    <tr key={i}>
                      <td>{sl.service_name}</td>
                      <td>{sl.quantity}</td>
                      <td>{fmt(sl.unit_price)}</td>
                      <td>{fmt(sl.quantity * sl.unit_price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          <h4 className={s.sectionTitle} style={{ marginTop: "1.25rem" }}>Bank Details</h4>
          <div className={s.infoGrid}>
            <div><span className={s.infoLabel}>Bank</span><span className={s.infoValue}>{claim.bank_name}</span></div>
            <div><span className={s.infoLabel}>Account No</span><span className={s.infoValue}>{claim.account_number}</span></div>
            <div><span className={s.infoLabel}>Account Name</span><span className={s.infoValue}>{claim.account_name}</span></div>
          </div>

          {claim.reviewer_notes && (
            <div className={s.textBlock} style={{ marginTop: "1.25rem" }}>
              <span className={s.infoLabel}>Reviewer Notes</span>
              <p>{claim.reviewer_notes}</p>
            </div>
          )}
        </div>

        {/* Right column — Actions + Timeline */}
        <div>
          {/* Status Actions */}
          {actions.length > 0 && (
            <div className={s.card} style={{ marginBottom: "1rem" }}>
              <h4 className={s.sectionTitle}>Update Status</h4>

              <label className={s.actionLabel}>
                Approved Amount (NGN)
                <input
                  type="number"
                  value={approvedAmt}
                  onChange={(e) => setApprovedAmt(e.target.value)}
                  className={s.actionInput}
                  placeholder="Optional — set approved amount"
                  min="0"
                  step="0.01"
                />
              </label>

              <label className={s.actionLabel}>
                Reviewer Notes
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className={s.actionTextarea}
                  placeholder="Add notes about this decision..."
                  rows={3}
                />
              </label>

              <div className={s.actionBtns}>
                {actions.map((action) => (
                  <button
                    key={action.value}
                    onClick={() => handleStatusUpdate(action.value)}
                    disabled={updating}
                    className={`${s.actionBtn} ${
                      action.value === "approved" ? s.actionBtnApprove :
                      action.value === "rejected" ? s.actionBtnReject :
                      s.actionBtnDefault
                    }`}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className={s.card}>
            <h4 className={s.sectionTitle}>Timeline</h4>
            {timeline.length === 0 ? (
              <p style={{ color: "#888", fontSize: "0.85rem" }}>No activity yet</p>
            ) : (
              <div className={s.timeline}>
                {timeline.map((entry, i) => (
                  <div key={entry.id} className={s.timelineItem}>
                    <div className={s.timelineDot} />
                    {i < timeline.length - 1 && <div className={s.timelineLine} />}
                    <div className={s.timelineContent}>
                      <div className={s.timelineAction}>
                        <strong>{entry.action.replace(/_/g, " ")}</strong>
                        <span className={s.timelineActor}>
                          by {entry.actor_type} {entry.actor_id?.substring(0, 8)}
                        </span>
                      </div>
                      <div className={s.timelineDate}>{fmtDate(entry.created_at)}</div>
                      {entry.details && (
                        <div className={s.timelineDetails}>
                          {entry.details.old_status && (
                            <span>{statusLabel(entry.details.old_status)} → {statusLabel(entry.details.new_status)}</span>
                          )}
                          {entry.details.reviewer_notes && <span>Note: {entry.details.reviewer_notes}</span>}
                          {entry.details.amount_flag && <span className={s.timelineFlag}>{entry.details.amount_flag}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
