import React, { useEffect, useState } from "react";
import { listMyCodes } from "../services/agentApi";
import styles from "./callcenter.module.css";

const STATUS_CONFIG = {
  active: { label: "Active", className: "statusActive" },
  used: { label: "Used", className: "statusUsed" },
  expired: { label: "Expired", className: "statusExpired" },
};

export default function CodeHistory({ refreshKey }) {
  const [codes, setCodes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCodes();
  }, [refreshKey]);

  const loadCodes = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await listMyCodes(0, 50);
      setCodes(data.codes);
      setTotal(data.total);
    } catch (err) {
      setError("Failed to load code history");
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount) =>
    new Intl.NumberFormat("en-NG", {
      style: "currency",
      currency: "NGN",
    }).format(amount);

  const formatDate = (dateStr) =>
    new Date(dateStr).toLocaleString("en-NG", {
      dateStyle: "short",
      timeStyle: "short",
    });

  if (loading) {
    return (
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Authorization Code History</h3>
        <div className={styles.loadingState}>Loading codes...</div>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div>
          <h3 className={styles.cardTitle}>Authorization Code History</h3>
          <p className={styles.cardSubtitle}>
            {total} code{total !== 1 ? "s" : ""} generated
          </p>
        </div>
        <button onClick={loadCodes} className={styles.refreshBtn} title="Refresh">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
          </svg>
        </button>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {codes.length === 0 ? (
        <div className={styles.emptyState}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" strokeWidth="1.5">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p>No codes generated yet</p>
          <span>Use the form above to generate your first authorization code</span>
        </div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Code</th>
                <th>Member</th>
                <th>Amount</th>
                <th>Visit Type</th>
                <th>Status</th>
                <th>Created</th>
                <th>Expires</th>
              </tr>
            </thead>
            <tbody>
              {codes.map((code) => {
                const cfg = STATUS_CONFIG[code.status] || STATUS_CONFIG.active;
                return (
                  <tr key={code.id}>
                    <td>
                      <span className={styles.codeCell}>{code.code}</span>
                    </td>
                    <td>
                      <div className={styles.memberCell}>
                        <span className={styles.memberName}>
                          {code.member_name || "—"}
                        </span>
                        <span className={styles.memberId}>{code.enrollee_id}</span>
                      </div>
                    </td>
                    <td className={styles.amountCell}>
                      {formatAmount(code.approved_amount)}
                    </td>
                    <td>{code.visit_type}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${styles[cfg.className]}`}>
                        {cfg.label}
                      </span>
                    </td>
                    <td className={styles.dateCell}>{formatDate(code.created_at)}</td>
                    <td className={styles.dateCell}>{formatDate(code.expires_at)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
