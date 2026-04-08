import React, { useEffect, useState } from "react";
import { listClaims, exportClaimsExcel } from "../services/claimsApi";
import s from "./claimsportal.module.css";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "submitted", label: "Submitted" },
  { value: "under_review", label: "Under Review" },
  { value: "pending_info", label: "Pending Info" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
  { value: "payment_processing", label: "Payment Processing" },
  { value: "paid", label: "Paid" },
];

const STATUS_STYLES = {
  submitted: "statusSubmitted",
  under_review: "statusReview",
  pending_info: "statusPending",
  approved: "statusApproved",
  rejected: "statusRejected",
  payment_processing: "statusProcessing",
  paid: "statusPaid",
};

export default function ClaimsTable({ onSelectClaim, refreshKey }) {
  const [claims, setClaims] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadClaims();
  }, [statusFilter, refreshKey]);

  const loadClaims = async () => {
    setLoading(true);
    try {
      const { data } = await listClaims({ status: statusFilter || undefined, search: search || undefined });
      setClaims(data.claims);
      setTotal(data.total);
    } catch {
      setClaims([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadClaims();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await exportClaimsExcel(statusFilter || undefined);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `claims_export_${new Date().toISOString().slice(0, 10)}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Export failed. Please try again.");
    } finally {
      setExporting(false);
    }
  };

  const fmt = (amount) =>
    new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" }).format(amount);

  const fmtDate = (d) =>
    new Date(d).toLocaleDateString("en-NG", { dateStyle: "medium" });

  const statusLabel = (st) => st.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className={s.card}>
      {/* Toolbar */}
      <div className={s.toolbar}>
        <div className={s.toolbarLeft}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={s.filterSelect}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <form onSubmit={handleSearch} className={s.searchForm}>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={s.searchInput}
              placeholder="Search by ref, enrollee ID, or name..."
            />
            <button type="submit" className={s.searchBtn}>Search</button>
          </form>
        </div>

        <div className={s.toolbarRight}>
          <span className={s.totalCount}>{total} claim{total !== 1 ? "s" : ""}</span>
          <button onClick={handleExport} disabled={exporting} className={s.exportBtn}>
            {exporting ? "Exporting..." : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Export Excel
              </>
            )}
          </button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className={s.loadingState}>Loading claims...</div>
      ) : claims.length === 0 ? (
        <div className={s.emptyState}>
          <p>No claims found</p>
          <span>Adjust your filters or wait for new submissions</span>
        </div>
      ) : (
        <div className={s.tableWrap}>
          <table className={s.table}>
            <thead>
              <tr>
                <th>Claim Ref</th>
                <th>Member</th>
                <th>Auth Code</th>
                <th>Amount</th>
                <th>Hospital</th>
                <th>Status</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c) => (
                <tr
                  key={c.claim_id}
                  onClick={() => onSelectClaim(c.claim_id)}
                  className={s.clickableRow}
                >
                  <td><span className={s.refCell}>{c.claim_ref}</span></td>
                  <td>
                    <div className={s.memberCell}>
                      <span className={s.memberCellName}>{c.member_name}</span>
                      <span className={s.memberCellId}>{c.enrollee_id}</span>
                    </div>
                  </td>
                  <td><span className={s.codeCell}>{c.authorization_code || "—"}</span></td>
                  <td className={s.amountCell}>{fmt(c.claim_amount)}</td>
                  <td className={s.hospitalCell}>{c.hospital_name}</td>
                  <td>
                    <span className={`${s.statusBadge} ${s[STATUS_STYLES[c.status]] || ""}`}>
                      {statusLabel(c.status)}
                    </span>
                  </td>
                  <td className={s.dateCell}>{fmtDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
