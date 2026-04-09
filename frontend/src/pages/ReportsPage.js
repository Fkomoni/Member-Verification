import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./ReportsPage.module.css";

const ROUTE_LABELS = { wellahealth: "WellaHealth", whatsapp_lagos: "WhatsApp (Lagos)", whatsapp_outside_lagos: "WhatsApp (Outside Lagos)", manual_review: "Manual Review" };
const CLS_LABELS = { acute: "Acute", chronic: "Chronic", mixed: "Mixed", review_required: "Review" };

export default function ReportsPage() {
  const { provider, logout } = useAuth();
  const [days, setDays] = useState("");
  const [summary, setSummary] = useState(null);
  const [byProvider, setByProvider] = useState([]);
  const [byRoute, setByRoute] = useState([]);
  const [topDrugs, setTopDrugs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = days ? { days } : {};
    setLoading(true);
    Promise.all([
      api.get("/reports/summary", { params }),
      api.get("/reports/by-provider", { params }),
      api.get("/reports/by-route", { params }),
      api.get("/reports/top-drugs", { params: { ...params, limit: 15 } }),
    ]).then(([s, p, r, d]) => {
      setSummary(s.data);
      setByProvider(p.data);
      setByRoute(r.data);
      setTopDrugs(d.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [days]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <Link to="/dashboard" className={styles.headerLogo}>
            <img src={logo} alt="Leadway Health" className={styles.headerLogoImg} />
          </Link>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Reports</span>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.providerName}>{provider?.provider_name}</span>
          <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
        </div>
      </header>

      <nav className={styles.navBar}>
        
        <Link to="/medication-request" className={styles.navLink}>New Rx Request</Link>
        <Link to="/medication-requests" className={styles.navLink}>Request History</Link>
        <Link to="/admin/review" className={styles.navLink}>Review Queue</Link>
        <Link to="/reports" className={styles.navLinkActive}>Reports</Link>
      </nav>

      <main className={styles.main}>
        <div className={styles.titleRow}>
          <h1 className={styles.pageTitle}>Reports & Analytics</h1>
          <select className={styles.periodSelect} value={days} onChange={(e) => setDays(e.target.value)}>
            <option value="">All Time</option>
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
          </select>
        </div>

        {loading ? <div className={styles.loading}>Loading...</div> : (
          <>
            {/* Metric Cards */}
            {summary && (
              <div className={styles.metricsRow}>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.total_requests}</div>
                  <div className={styles.metricLabel}>Total Requests</div>
                </div>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.by_classification?.acute || 0}</div>
                  <div className={styles.metricLabel}>Acute</div>
                </div>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.by_classification?.chronic || 0}</div>
                  <div className={styles.metricLabel}>Chronic</div>
                </div>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.by_classification?.mixed || 0}</div>
                  <div className={styles.metricLabel}>Mixed</div>
                </div>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.location?.lagos || 0}</div>
                  <div className={styles.metricLabel}>Lagos</div>
                </div>
                <div className={styles.metricCard}>
                  <div className={styles.metricValue}>{summary.location?.outside_lagos || 0}</div>
                  <div className={styles.metricLabel}>Outside Lagos</div>
                </div>
              </div>
            )}

            <div className={styles.chartsGrid}>
              {/* Routing Breakdown */}
              <div className={styles.chartCard}>
                <h3 className={styles.chartTitle}>Routing Breakdown</h3>
                {byRoute.length === 0 ? <div className={styles.noData}>No data</div> :
                  byRoute.map((r) => (
                    <div key={r.destination} className={styles.barRow}>
                      <span className={styles.barLabel}>{ROUTE_LABELS[r.destination] || r.destination}</span>
                      <div className={styles.barTrack}>
                        <div className={styles.barFill} style={{ width: `${Math.max(5, (r.count / (summary?.total_requests || 1)) * 100)}%` }} />
                      </div>
                      <span className={styles.barCount}>{r.count}</span>
                    </div>
                  ))
                }
              </div>

              {/* Status Breakdown */}
              {summary?.by_status && (
                <div className={styles.chartCard}>
                  <h3 className={styles.chartTitle}>Status Breakdown</h3>
                  {Object.entries(summary.by_status).map(([status, count]) => (
                    <div key={status} className={styles.barRow}>
                      <span className={styles.barLabel}>{status.replace(/_/g, " ")}</span>
                      <div className={styles.barTrack}>
                        <div className={styles.barFill} style={{ width: `${Math.max(5, (count / summary.total_requests) * 100)}%` }} />
                      </div>
                      <span className={styles.barCount}>{count}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* By Provider */}
              <div className={styles.chartCard}>
                <h3 className={styles.chartTitle}>By Provider</h3>
                {byProvider.length === 0 ? <div className={styles.noData}>No data</div> :
                  byProvider.slice(0, 10).map((p, i) => (
                    <div key={i} className={styles.barRow}>
                      <span className={styles.barLabel}>{p.provider_name}</span>
                      <div className={styles.barTrack}>
                        <div className={styles.barFill} style={{ width: `${Math.max(5, (p.total_requests / (byProvider[0]?.total_requests || 1)) * 100)}%` }} />
                      </div>
                      <span className={styles.barCount}>{p.total_requests}</span>
                    </div>
                  ))
                }
              </div>

              {/* Top Drugs */}
              <div className={styles.chartCard}>
                <h3 className={styles.chartTitle}>Top Medications</h3>
                {topDrugs.length === 0 ? <div className={styles.noData}>No data</div> :
                  topDrugs.map((d, i) => (
                    <div key={i} className={styles.barRow}>
                      <span className={styles.barLabel}>
                        {d.drug_name}
                        {d.category && <span className={styles.drugCat}>{d.category}</span>}
                      </span>
                      <span className={styles.barCount}>{d.count}</span>
                    </div>
                  ))
                }
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
