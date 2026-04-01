import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [memberId, setMemberId] = useState('');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('login'); // login | otp
  const [phoneMasked, setPhoneMasked] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, sendOtp, verifyOtp } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await login(memberId.trim(), phone.trim());
      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed';
      setError(msg);
      // Offer OTP fallback
      try {
        const res = await sendOtp(memberId.trim());
        setPhoneMasked(res.phone_masked);
        setStep('otp');
        setError('');
      } catch (otpErr) {
        setError(msg + '. OTP fallback also failed.');
      }
    } finally { setLoading(false); }
  };

  const handleOtp = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      await verifyOtp(memberId.trim(), otp);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally { setLoading(false); }
  };

  return (
    <div style={s.container}>
      <div style={s.card}>
        <div style={s.logoWrap}>
          <div style={s.logo}>Rx</div>
          <h1 style={s.title}>LeadwayHMO RxHub</h1>
          <p style={s.sub}>Member Self-Service Portal</p>
        </div>

        {error && <div style={s.error}>{error}</div>}

        {step === 'login' ? (
          <form onSubmit={handleLogin} style={s.form}>
            <label style={s.label}>Member ID</label>
            <input style={s.input} value={memberId} onChange={e => setMemberId(e.target.value)} placeholder="e.g. 21000645/0" required />
            <label style={s.label}>Phone Number</label>
            <input style={s.input} value={phone} onChange={e => setPhone(e.target.value)} placeholder="e.g. 08012345678" required />
            <button type="submit" disabled={loading} style={s.btn}>{loading ? 'Verifying...' : 'Sign In'}</button>
          </form>
        ) : (
          <form onSubmit={handleOtp} style={s.form}>
            <p style={{ fontSize: 14, color: '#666', marginBottom: 16 }}>OTP sent to <strong>{phoneMasked}</strong></p>
            <label style={s.label}>Enter OTP</label>
            <input style={{ ...s.input, textAlign: 'center', fontSize: 22, letterSpacing: 6 }} value={otp} onChange={e => setOtp(e.target.value)} maxLength={6} required />
            <button type="submit" disabled={loading} style={s.btn}>{loading ? 'Verifying...' : 'Verify OTP'}</button>
            <button type="button" onClick={() => setStep('login')} style={s.backBtn}>Back to login</button>
          </form>
        )}
      </div>
    </div>
  );
}

const s = {
  container: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1A1A2E' },
  card: { backgroundColor: '#fff', borderRadius: 16, padding: '40px 36px', width: 400, boxShadow: '0 20px 60px rgba(0,0,0,0.3)' },
  logoWrap: { textAlign: 'center', marginBottom: 28 },
  logo: { width: 52, height: 52, borderRadius: 13, backgroundColor: '#C8102E', color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 20, marginBottom: 10 },
  title: { fontSize: 22, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { fontSize: 13, color: '#666', marginTop: 4 },
  form: { display: 'flex', flexDirection: 'column', gap: 10 },
  label: { fontSize: 13, fontWeight: 600, color: '#333' },
  input: { padding: '12px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14, outline: 'none' },
  btn: { padding: '13px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E', color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer', marginTop: 6 },
  backBtn: { background: 'none', border: 'none', color: '#C8102E', cursor: 'pointer', fontSize: 13, marginTop: 8 },
  error: { backgroundColor: '#FEE2E2', color: '#C8102E', padding: '10px 14px', borderRadius: 8, fontSize: 13, marginBottom: 12, textAlign: 'center' },
};
