import React, { useState } from "react";
import { getClaimsStatus } from "../services/api";
import styles from "./ClaimsStatus.module.css";
import shared from "./shared.module.css";

export default function ClaimsStatus({ enrolleeId, onClose }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  const handleFetch = async () => {
    setError("");
    setLoading(true);
    try {
      const { data: result } = await getClaimsStatus(enrolleeId);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to fetch claims");
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on first render
  React.useEffect(() => {
    if (enrolleeId) handleFetch();
  }, [enrolleeId]);

  return (
    <div className={shared.card}>
      <div className={styles.header}>
        <div>
          <h3 className={shared.cardTitle}>Reimbursement Claims</h3>
          <p className={shared.cardSubtitle}>
            Claims status for enrollee {enrolleeId}
          </p>
        </div>
        {onClose && (
          <button onClick={onClose} className={shared.secondaryBtn} style={{ marginTop: 0 }}>
            Back
          </button>
        )}
      </div>

      {error && <div className={shared.error}>{error}</div>}

      {loading && <p className={styles.loading}>Loading claims...</p>}

      {data && !loading && (
        <>
          <div className={styles.summary}>
            <div className={styles.summaryItem}>
              <span className={shared.detailLabel}>Total Claims</span>
              <span className={styles.summaryValue}>{data.total_claims}</span>
            </div>
            <div className={styles.summaryItem}>
              <span className={shared.detailLabel}>Status</span>
              <span className={styles.summaryValue}>
                {data.success ? "Retrieved" : "Failed"}
              </span>
            </div>
          </div>

          {data.reason && data.total_claims === 0 && (
            <p className={styles.noData}>{data.reason}</p>
          )}

          {data.claims.length > 0 && (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Claim ID</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Amount</th>
                    <th>Provider</th>
                  </tr>
                </thead>
                <tbody>
                  {data.claims.map((claim, idx) => (
                    <tr key={claim.claimId || claim.ClaimId || claim.id || idx}>
                      <td>{claim.claimId || claim.ClaimId || claim.id || "-"}</td>
                      <td>
                        {claim.claimDate || claim.ClaimDate || claim.date
                          ? new Date(claim.claimDate || claim.ClaimDate || claim.date).toLocaleDateString()
                          : "-"}
                      </td>
                      <td>
                        <span
                          className={`${styles.claimBadge} ${
                            (claim.status || claim.Status || "").toLowerCase() === "approved"
                              ? styles.badgeApproved
                              : (claim.status || claim.Status || "").toLowerCase() === "pending"
                              ? styles.badgePending
                              : (claim.status || claim.Status || "").toLowerCase() === "rejected" ||
                                (claim.status || claim.Status || "").toLowerCase() === "denied"
                              ? styles.badgeRejected
                              : styles.badgeDefault
                          }`}
                        >
                          {claim.status || claim.Status || "N/A"}
                        </span>
                      </td>
                      <td>{claim.amount || claim.Amount || claim.claimAmount || claim.ClaimAmount || "-"}</td>
                      <td>{claim.providerName || claim.ProviderName || claim.provider || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <button onClick={handleFetch} disabled={loading} className={shared.secondaryBtn}>
            Refresh
          </button>
        </>
      )}
    </div>
  );
}
