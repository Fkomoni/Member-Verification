import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAgentAuth } from "../context/AgentAuthContext";
import styles from "./CallCenterLoginPage.module.css";

export default function ClaimsLoginPage() {
  const { login } = useAgentAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <div className={styles.brandContent}>
          <div className={styles.logoBlock}>
            <img src="/leadway-logo.png" alt="Leadway Health HMO" style={{ height: 52, width: "auto", filter: "brightness(0) invert(1)" }} />
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
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className={styles.input} placeholder="Enter password" />
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
