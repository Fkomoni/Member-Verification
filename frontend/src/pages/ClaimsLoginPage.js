import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAgentAuth } from "../context/AgentAuthContext";
import styles from "./CallCenterLoginPage.module.css";

export default function ClaimsLoginPage() {
  const { login } = useAgentAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      if (data.role !== "claims_officer" && data.role !== "admin") {
        setError("Access denied. Claims officer or admin role required.");
        return;
      }
      navigate("/claims/dashboard");
    } catch (err) {
      if (err.response) {
        setError(err.response.data?.detail || `Server error (${err.response.status})`);
      } else if (err.request) {
        setError("Cannot reach the server. Please check your connection or try again later.");
      } else {
        setError(err.message || "Login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <div className={styles.brandContent}>
          <div className={styles.logoBlock}>
            <img src="/leadway-logo.png" alt="Leadway Health HMO" className={styles.logoImg} />
          </div>
          <h1 className={styles.brandTitle}>Claims Portal</h1>
          <p className={styles.brandTagline}>
            Review, track, and manage reimbursement claims.
            Full visibility into the claims pipeline with export capabilities.
          </p>
        </div>
      </div>

      <div className={styles.rightPanel}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <h2 className={styles.formTitle}>Claims Team Sign In</h2>
          <p className={styles.formSubtitle}>
            Access the claims review and management system
          </p>

          {error && <div className={styles.error}>{error}</div>}

          <label className={styles.label}>
            Email Address
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className={styles.input} placeholder="claims@leadwayhealth.com" />
          </label>

          <label className={styles.label}>
            Password
            <div className={styles.passwordWrap}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className={styles.input}
                placeholder="Enter password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className={styles.eyeBtn}
                tabIndex={-1}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#888" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </label>

          <button type="submit" disabled={loading} className={styles.button}>
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <p className={styles.footer}>
            Leadway Health Services &mdash; For health, wealth &amp; more...
          </p>
        </form>
      </div>
    </div>
  );
}
