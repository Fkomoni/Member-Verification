import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const TYPES = [
  { key: 'BLOOD_PRESSURE', label: 'Blood Pressure', unit: 'mmHg' },
  { key: 'BLOOD_GLUCOSE', label: 'Blood Glucose', unit: 'mg/dL' },
  { key: 'CHOLESTEROL', label: 'Cholesterol', unit: 'mg/dL' },
];

const GLUCOSE_CTX = ['FASTING', 'RANDOM', 'POST_MEAL'];

export default function HealthReadingsPage() {
  const [latest, setLatest] = useState({});
  const [history, setHistory] = useState([]);
  const [historyType, setHistoryType] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState('BLOOD_PRESSURE');
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchLatest = useCallback(() => {
    api.get('/health-readings/latest').then(r => setLatest(r.data)).catch(() => {});
  }, []);

  const fetchHistory = useCallback(() => {
    const params = { limit: 20 };
    if (historyType) params.reading_type = historyType;
    api.get('/health-readings', { params }).then(r => setHistory(r.data)).catch(() => {});
  }, [historyType]);

  useEffect(() => { fetchLatest(); fetchHistory(); }, [fetchLatest, fetchHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/health-readings', { reading_type: formType, ...form });
      setShowForm(false);
      setForm({});
      fetchLatest();
      fetchHistory();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save reading');
    } finally { setSaving(false); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={s.heading}>Health Readings</h1>
          <p style={s.sub}>Track your blood pressure, glucose, and cholesterol</p>
        </div>
        <button style={s.addBtn} onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Log Reading'}
        </button>
      </div>

      {/* ── Entry Form ── */}
      {showForm && (
        <form onSubmit={handleSubmit} style={s.formCard}>
          <div style={s.formTitle}>New Reading</div>

          <div style={s.typeRow}>
            {TYPES.map(t => (
              <button key={t.key} type="button"
                style={{ ...s.typeBtn, ...(formType === t.key ? s.typeBtnActive : {}) }}
                onClick={() => { setFormType(t.key); setForm({}); }}>
                {t.label}
              </button>
            ))}
          </div>

          {formType === 'BLOOD_PRESSURE' && (
            <div style={s.fieldRow}>
              <div style={s.field}>
                <label style={s.label}>Systolic (top)</label>
                <input style={s.input} type="number" placeholder="e.g. 120" required
                  value={form.systolic || ''} onChange={e => setForm({ ...form, systolic: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Diastolic (bottom)</label>
                <input style={s.input} type="number" placeholder="e.g. 80" required
                  value={form.diastolic || ''} onChange={e => setForm({ ...form, diastolic: e.target.value })} />
              </div>
            </div>
          )}

          {formType === 'BLOOD_GLUCOSE' && (
            <div style={s.fieldRow}>
              <div style={s.field}>
                <label style={s.label}>Glucose Level (mg/dL)</label>
                <input style={s.input} type="number" placeholder="e.g. 95" required
                  value={form.glucose_level || ''} onChange={e => setForm({ ...form, glucose_level: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Context</label>
                <select style={s.input} value={form.glucose_context || ''}
                  onChange={e => setForm({ ...form, glucose_context: e.target.value })}>
                  <option value="">Select...</option>
                  {GLUCOSE_CTX.map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
                </select>
              </div>
            </div>
          )}

          {formType === 'CHOLESTEROL' && (
            <div style={s.fieldRow}>
              <div style={s.field}>
                <label style={s.label}>Total Cholesterol</label>
                <input style={s.input} type="number" placeholder="e.g. 200" required
                  value={form.total_cholesterol || ''} onChange={e => setForm({ ...form, total_cholesterol: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>HDL</label>
                <input style={s.input} type="number" placeholder="e.g. 55"
                  value={form.hdl || ''} onChange={e => setForm({ ...form, hdl: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>LDL</label>
                <input style={s.input} type="number" placeholder="e.g. 130"
                  value={form.ldl || ''} onChange={e => setForm({ ...form, ldl: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Triglycerides</label>
                <input style={s.input} type="number" placeholder="e.g. 150"
                  value={form.triglycerides || ''} onChange={e => setForm({ ...form, triglycerides: e.target.value })} />
              </div>
            </div>
          )}

          <label style={s.label}>Notes (optional)</label>
          <input style={s.input} placeholder="e.g. Taken after breakfast"
            value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />

          <button type="submit" disabled={saving} style={s.saveBtn}>{saving ? 'Saving...' : 'Save Reading'}</button>
        </form>
      )}

      {/* ── Latest Readings Cards ── */}
      <div style={s.latestGrid}>
        {TYPES.map(t => {
          const r = latest[t.key];
          return (
            <div key={t.key} style={s.latestCard}>
              <div style={s.latestType}>{t.label}</div>
              {r ? (
                <>
                  <div style={s.latestValue}>
                    {t.key === 'BLOOD_PRESSURE' && `${r.systolic}/${r.diastolic}`}
                    {t.key === 'BLOOD_GLUCOSE' && `${r.glucose_level}`}
                    {t.key === 'CHOLESTEROL' && `${r.total_cholesterol}`}
                  </div>
                  <div style={s.latestUnit}>{t.unit}</div>
                  {t.key === 'BLOOD_GLUCOSE' && r.glucose_context && <div style={s.ctx}>{r.glucose_context.replace('_', ' ')}</div>}
                  {t.key === 'CHOLESTEROL' && r.hdl && <div style={s.ctx}>HDL: {r.hdl} / LDL: {r.ldl}</div>}
                  <div style={s.latestDate}>{new Date(r.recorded_at).toLocaleDateString()}</div>
                </>
              ) : (
                <div style={s.noData}>No readings yet</div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── History ── */}
      <div style={{ marginTop: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={s.sectionTitle}>History</h2>
          <div style={{ display: 'flex', gap: 6 }}>
            {[{ key: '', label: 'All' }, ...TYPES].map(t => (
              <button key={t.key} onClick={() => setHistoryType(t.key)}
                style={{ ...s.filterBtn, ...(historyType === t.key ? { backgroundColor: '#1A1A2E', color: '#fff' } : {}) }}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div style={s.table}>
          <div style={s.tableHead}>
            <span>Date</span><span>Type</span><span>Reading</span><span>Notes</span>
          </div>
          {history.map(r => (
            <div key={r.id} style={s.tableRow}>
              <span>{new Date(r.recorded_at).toLocaleString()}</span>
              <span>{r.reading_type.replace('_', ' ')}</span>
              <span style={{ fontWeight: 600 }}>
                {r.reading_type === 'BLOOD_PRESSURE' && `${r.systolic}/${r.diastolic} mmHg`}
                {r.reading_type === 'BLOOD_GLUCOSE' && `${r.glucose_level} mg/dL ${r.glucose_context ? `(${r.glucose_context.replace('_', ' ')})` : ''}`}
                {r.reading_type === 'CHOLESTEROL' && `${r.total_cholesterol} mg/dL (HDL:${r.hdl || '-'} LDL:${r.ldl || '-'})`}
              </span>
              <span style={{ color: '#666' }}>{r.notes || '-'}</span>
            </div>
          ))}
          {history.length === 0 && <div style={{ padding: 30, textAlign: 'center', color: '#999' }}>No readings recorded yet</div>}
        </div>
      </div>
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, fontSize: 14 },
  addBtn: { padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
  formCard: { backgroundColor: '#fff', borderRadius: 12, padding: 24, marginBottom: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', gap: 12 },
  formTitle: { fontSize: 16, fontWeight: 700, color: '#1A1A2E' },
  typeRow: { display: 'flex', gap: 8 },
  typeBtn: { padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  typeBtnActive: { backgroundColor: '#1A1A2E', color: '#fff', borderColor: '#1A1A2E' },
  fieldRow: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 },
  field: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 12, fontWeight: 600, color: '#444' },
  input: { padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14 },
  saveBtn: { padding: '12px', borderRadius: 8, border: 'none', backgroundColor: '#1A1A2E', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', marginTop: 4 },
  latestGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 },
  latestCard: { backgroundColor: '#fff', borderRadius: 12, padding: 22, textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  latestType: { fontSize: 12, fontWeight: 700, color: '#E87722', textTransform: 'uppercase', letterSpacing: 0.5 },
  latestValue: { fontSize: 36, fontWeight: 700, color: '#1A1A2E', marginTop: 8 },
  latestUnit: { fontSize: 13, color: '#999' },
  ctx: { fontSize: 12, color: '#666', marginTop: 4 },
  latestDate: { fontSize: 12, color: '#999', marginTop: 6 },
  noData: { fontSize: 14, color: '#ccc', marginTop: 20, marginBottom: 10 },
  sectionTitle: { fontSize: 18, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  filterBtn: { padding: '6px 12px', borderRadius: 6, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 500 },
  table: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  tableHead: { display: 'grid', gridTemplateColumns: '160px 140px 1fr 1fr', padding: '12px 18px', backgroundColor: '#F8F8FA', fontSize: 12, fontWeight: 600, color: '#666' },
  tableRow: { display: 'grid', gridTemplateColumns: '160px 140px 1fr 1fr', padding: '12px 18px', borderTop: '1px solid #f0f0f0', fontSize: 13 },
};
