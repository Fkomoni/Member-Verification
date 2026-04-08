import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import styles from "./LoginPage.module.css";

export default function ClaimsLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const { data } = await api.post("/claims/login", { email, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("claims_officer", JSON.stringify({
        agent_id: data.agent_id, agent_name: data.agent_name, role: data.role,
      }));
      navigate("/claims/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <div className={styles.brandContent}>
          <div className={styles.logoBlock}>
            <div className={styles.camelIcon}>
              <svg viewBox="0 0 60 60" width="48" height="48">
                <circle cx="30" cy="30" r="28" fill="url(#sunGrad3)" />
                <defs><linearGradient id="sunGrad3" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#F15A24" /><stop offset="100%" stopColor="#FFCE07" /></linearGradient></defs>
              </svg>
            </div>
            <div className={styles.logoText}>
              <span className={styles.logoLeadway}>LEADWAY</span>
              <span className={styles.logoHealth}>Health</span>
            </div>
          </div>
          <h1 className={styles.brandTitle}>Claims Review Portal</h1>
          <p className={styles.brandTagline}>Review, verify, and process member reimbursement claims.</p>
        </div>
      </div>
      <div className={styles.rightPanel}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <h2 className={styles.formTitle}>Claims Officer Sign In</h2>
          <p className={styles.formSubtitle}>Access the claims review dashboard</p>
          {error && <div className={styles.error}>{error}</div>}
          <label className={styles.label}>Email Address
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className={styles.input} placeholder="claims@leadway.com" />
          </label>
          <label className={styles.label}>Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className={styles.input} placeholder="Enter password" />
          </label>
          <button type="submit" disabled={loading} className={styles.button}>{loading ? "Signing in..." : "Sign In"}</button>
          <p className={styles.footer}>Leadway Health Services &mdash; For health, wealth &amp; more...</p>
        </form>
      </div>
    </div>
  );
}
