import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logoWrap}>
          <img src="/leadway-logo.jpg" alt="Leadway Health" style={styles.logoImg} />
          <h1 style={styles.title}>RxHub Admin</h1>
          <p style={styles.subtitle}>Leadway Health HMO — Management Portal</p>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          {error && <div style={styles.error}>{error}</div>}

          <label style={styles.label}>Email</label>
          <input
            type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            required style={styles.input} placeholder="admin@leadwayhmo.com"
          />

          <label style={styles.label}>Password</label>
          <input
            type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            required style={styles.input} placeholder="Enter password"
          />

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    backgroundColor: '#262626', fontFamily: "'Inter', sans-serif",
  },
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: '48px 40px', width: 400,
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  logoWrap: { textAlign: 'center', marginBottom: 32 },
  logoImg: { width: 220, height: 'auto', marginBottom: 12 },
  title: { fontSize: 24, fontWeight: 700, color: '#C8102E', margin: 0 },
  subtitle: { fontSize: 14, color: '#666', marginTop: 4 },
  form: { display: 'flex', flexDirection: 'column', gap: 12 },
  label: { fontSize: 13, fontWeight: 600, color: '#333' },
  input: {
    padding: '12px 16px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14,
    outline: 'none', transition: 'border 0.2s',
  },
  button: {
    padding: '14px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E',
    color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: 8,
  },
  error: {
    backgroundColor: '#FEE2E2', color: '#C8102E', padding: '10px 14px',
    borderRadius: 8, fontSize: 13, textAlign: 'center',
  },
};
