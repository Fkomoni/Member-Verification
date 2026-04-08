import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./LoginPage.module.css";

export default function LoginPage() {
  const { login } = useAuth();
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
      await login(email, password);
      navigate("/dashboard");
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
          <h1 className={styles.brandTitle}>Member Verification Portal</h1>
          <p className={styles.brandTagline}>
            Biometric identity verification for healthcare providers.
            Secure. Real-time. Fraud-proof.
          </p>
        </div>
      </div>

      <div className={styles.rightPanel}>
        <form className={styles.form} onSubmit={handleSubmit}>
          <h2 className={styles.formTitle}>Provider Sign In</h2>
          <p className={styles.formSubtitle}>
            Access your verification dashboard
          </p>

          {error && <div className={styles.error}>{error}</div>}

          <label className={styles.label}>
            Email Address
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={styles.input}
              placeholder="provider@facility.com"
            />
          </label>

          <label className={styles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className={styles.input}
              placeholder="Enter password"
            />
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
