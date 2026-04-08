import React, { useState, useEffect } from "react";
import { useAgentAuth } from "../context/AgentAuthContext";
import { getClaimsStats } from "../services/claimsApi";
import ClaimsTable from "../components/ClaimsTable";
import ClaimDetail from "../components/ClaimDetail";
import s from "../components/claimsportal.module.css";
import styles from "./ClaimsPortalPage.module.css";

export default function ClaimsPortalPage() {
  const { agent, logout } = useAgentAuth();
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStats();
  }, [refreshKey]);

  const loadStats = async () => {
    try {
      const { data } = await getClaimsStats();
      setStats(data);
    } catch {
      // Stats are nice-to-have
    }
  };

  const fmt = (amount) =>
    new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(amount);

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.headerLogo}>
            <svg viewBox="0 0 40 40" width="32" height="32">
              <circle cx="20" cy="20" r="18" fill="url(#cpGrad)" />
              <defs>
                <linearGradient id="cpGrad" x1="0" y1="0" x2="0" y2="1">
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
          <span className={styles.headerPortal}>Claims Portal</span>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.agentInfo}>
            <span className={styles.agentName}>{agent?.agent_name}</span>
            <span className={styles.agentRole}>
              {agent?.role === "claims_officer" ? "Claims Officer" : agent?.role === "admin" ? "Administrator" : agent?.role}
            </span>
          </div>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <main className={styles.main}>
        {!selectedClaim ? (
          <>
            <h1 className={styles.pageTitle}>Claims Management</h1>

            {/* Stats */}
            {stats && (
              <div className={s.statsBar}>
                <div className={s.statCard}>
                  <div className={s.statLabel}>Total Claims</div>
                  <div className={s.statValue}>{stats.total_claims}</div>
                </div>
                <div className={s.statCard}>
                  <div className={s.statLabel}>Total Claim Amount</div>
                  <div className={s.statValue}>{fmt(stats.total_claim_amount)}</div>
                </div>
                <div className={s.statCard}>
                  <div className={s.statLabel}>Total Approved</div>
                  <div className={s.statValue}>{fmt(stats.total_approved_amount)}</div>
                </div>
                <div className={s.statCard}>
                  <div className={s.statLabel}>Pending Review</div>
                  <div className={s.statValueCrimson}>
                    {(stats.by_status?.submitted || 0) + (stats.by_status?.under_review || 0)}
                  </div>
                </div>
              </div>
            )}

            <ClaimsTable
              onSelectClaim={setSelectedClaim}
              refreshKey={refreshKey}
            />
          </>
        ) : (
          <ClaimDetail
            claimId={selectedClaim}
            onBack={() => setSelectedClaim(null)}
            onStatusChanged={() => setRefreshKey((k) => k + 1)}
          />
        )}
      </main>
    </div>
  );
}
