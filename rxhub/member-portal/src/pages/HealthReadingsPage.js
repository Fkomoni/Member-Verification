import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const TYPES = [
  { key: 'BLOOD_PRESSURE', label: 'Blood Pressure', unit: 'mmHg' },
  { key: 'BLOOD_GLUCOSE', label: 'Blood Glucose', unit: 'mg/dL' },
  { key: 'CHOLESTEROL', label: 'Cholesterol', unit: 'mg/dL' },
];

const GLUCOSE_CTX = ['FASTING', 'RANDOM', 'POST_MEAL'];

// Strip decimal points from readings
const n = (v) => v != null ? Math.round(parseFloat(v)) : v;

const TREND_ICONS = { IMPROVING: '\u2193', WORSENING: '\u2191', STABLE: '\u2194', NO_DATA: '-', INSUFFICIENT_DATA: '~' };
const TREND_COLORS = { IMPROVING: '#16A34A', WORSENING: '#DC2626', STABLE: '#2563EB', NO_DATA: '#999', INSUFFICIENT_DATA: '#999' };
const TREND_LABELS = { IMPROVING: 'Improving', WORSENING: 'Worsening', STABLE: 'Stable', NO_DATA: 'No data', INSUFFICIENT_DATA: 'Need more readings' };

export default function HealthReadingsPage() {
  const [latest, setLatest] = useState({});
  const [trends, setTrends] = useState({});
  const [history, setHistory] = useState([]);
  const [historyType, setHistoryType] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState('BLOOD_PRESSURE');
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchLatest = useCallback(() => {
    api.get('/health-readings/latest').then(r => setLatest(r.data)).catch(() => {});
  }, []);

  const fetchTrends = useCallback(() => {
    api.get('/health-readings/trends').then(r => setTrends(r.data)).catch(() => {});
  }, []);

  const fetchHistory = useCallback(() => {
    const params = { limit: 50 };
    if (historyType) params.reading_type = historyType;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    api.get('/health-readings', { params }).then(r => setHistory(r.data)).catch(() => {});
  }, [historyType, dateFrom, dateTo]);

  useEffect(() => { fetchLatest(); fetchTrends(); fetchHistory(); }, [fetchLatest, fetchTrends, fetchHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/health-readings', { reading_type: formType, ...form });
      setShowForm(false);
      setForm({});
      fetchLatest();
      fetchTrends();
      fetchHistory();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save reading');
    } finally { setSaving(false); }
  };

  const handleDownload = () => {
    const params = new URLSearchParams();
    if (historyType) params.set('reading_type', historyType);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    const token = localStorage.getItem('member_token');
    const url = `${api.defaults.baseURL}/health-readings/download?${params.toString()}`;
    // Use fetch for authenticated download
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `health_readings_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
      })
      .catch(() => alert('Download failed'));
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={s.heading}>Health Readings</h1>
          <p style={s.sub}>Track your blood pressure, glucose, and cholesterol over time</p>
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
                <input style={s.input} type="number" placeholder="e.g. 120" required value={form.systolic || ''} onChange={e => setForm({ ...form, systolic: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Diastolic (bottom)</label>
                <input style={s.input} type="number" placeholder="e.g. 80" required value={form.diastolic || ''} onChange={e => setForm({ ...form, diastolic: e.target.value })} />
              </div>
            </div>
          )}

          {formType === 'BLOOD_GLUCOSE' && (
            <div style={s.fieldRow}>
              <div style={s.field}>
                <label style={s.label}>Glucose Level (mg/dL)</label>
                <input style={s.input} type="number" placeholder="e.g. 95" required value={form.glucose_level || ''} onChange={e => setForm({ ...form, glucose_level: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Context</label>
                <select style={s.input} value={form.glucose_context || ''} onChange={e => setForm({ ...form, glucose_context: e.target.value })}>
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
                <input style={s.input} type="number" placeholder="e.g. 200" required value={form.total_cholesterol || ''} onChange={e => setForm({ ...form, total_cholesterol: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>HDL</label>
                <input style={s.input} type="number" placeholder="e.g. 55" value={form.hdl || ''} onChange={e => setForm({ ...form, hdl: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>LDL</label>
                <input style={s.input} type="number" placeholder="e.g. 130" value={form.ldl || ''} onChange={e => setForm({ ...form, ldl: e.target.value })} />
              </div>
              <div style={s.field}>
                <label style={s.label}>Triglycerides</label>
                <input style={s.input} type="number" placeholder="e.g. 150" value={form.triglycerides || ''} onChange={e => setForm({ ...form, triglycerides: e.target.value })} />
              </div>
            </div>
          )}

          <label style={s.label}>Notes (optional)</label>
          <input style={s.input} placeholder="e.g. Taken after breakfast" value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
          <button type="submit" disabled={saving} style={s.saveBtn}>{saving ? 'Saving...' : 'Save Reading'}</button>
        </form>
      )}

      {/* ── Trend Cards ── */}
      <div style={s.trendGrid}>
        {TYPES.map(t => {
          const r = latest[t.key];
          const tr = trends[t.key] || {};
          const trendColor = TREND_COLORS[tr.trend] || '#999';

          return (
            <div key={t.key} style={s.trendCard}>
              <div style={s.trendHeader}>
                <div style={s.trendType}>{t.label}</div>
                {tr.trend && tr.trend !== 'NO_DATA' && (
                  <div style={{ ...s.trendBadge, backgroundColor: trendColor + '18', color: trendColor, borderColor: trendColor + '40' }}>
                    <span style={{ fontSize: 14 }}>{TREND_ICONS[tr.trend]}</span> {TREND_LABELS[tr.trend]}
                  </div>
                )}
              </div>

              {r ? (
                <>
                  <div style={s.trendValue}>
                    {t.key === 'BLOOD_PRESSURE' && `${n(r.systolic)}/${n(r.diastolic)}`}
                    {t.key === 'BLOOD_GLUCOSE' && `${n(r.glucose_level)}`}
                    {t.key === 'CHOLESTEROL' && `${n(r.total_cholesterol)}`}
                  </div>
                  <div style={s.trendUnit}>{t.unit}</div>

                  {/* Classification */}
                  {tr.classification && (
                    <div style={{ ...s.classification,
                      color: tr.classification === 'NORMAL' || tr.classification === 'DESIRABLE' ? '#16A34A'
                           : tr.classification.includes('HIGH') || tr.classification.includes('DIABETIC') ? '#DC2626'
                           : '#E87722' }}>
                      {tr.classification}
                    </div>
                  )}

                  {/* Change from previous */}
                  {tr.change && (
                    <div style={s.changeRow}>
                      <span style={{ color: '#666', fontSize: 12 }}>vs previous: </span>
                      <span style={{ fontWeight: 600, fontSize: 13, color: trendColor }}>{tr.change}</span>
                    </div>
                  )}

                  {t.key === 'BLOOD_GLUCOSE' && r.glucose_context && <div style={s.ctx}>{r.glucose_context.replace('_', ' ')}</div>}
                  {t.key === 'CHOLESTEROL' && r.hdl && <div style={s.ctx}>HDL: {n(r.hdl)} / LDL: {n(r.ldl)}</div>}
                  <div style={s.trendDate}>{new Date(r.recorded_at).toLocaleDateString()}</div>
                  <div style={s.readingCount}>{tr.reading_count || 0} readings on file</div>
                </>
              ) : (
                <div style={s.noData}>No readings yet</div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── History with Date Range + Download ── */}
      <div style={{ marginTop: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h2 style={s.sectionTitle}>Reading History</h2>
          <button style={s.downloadBtn} onClick={handleDownload}>Download CSV</button>
        </div>

        {/* Filters */}
        <div style={s.filterRow}>
          <div style={s.filterGroup}>
            {[{ key: '', label: 'All' }, ...TYPES].map(t => (
              <button key={t.key} onClick={() => setHistoryType(t.key)}
                style={{ ...s.filterBtn, ...(historyType === t.key ? { backgroundColor: '#1A1A2E', color: '#fff' } : {}) }}>
                {t.label}
              </button>
            ))}
          </div>
          <div style={s.dateFilters}>
            <label style={s.dateLbl}>From</label>
            <input type="date" style={s.dateInput} value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
            <label style={s.dateLbl}>To</label>
            <input type="date" style={s.dateInput} value={dateTo} onChange={e => setDateTo(e.target.value)} />
            {(dateFrom || dateTo) && <button style={s.clearBtn} onClick={() => { setDateFrom(''); setDateTo(''); }}>Clear</button>}
          </div>
        </div>

        {/* Table */}
        <div style={s.table}>
          <div style={s.tableHead}>
            <span>Date &amp; Time</span><span>Type</span><span>Reading</span><span>Status</span><span>Notes</span>
          </div>
          {history.map((r, i) => {
            // Determine change arrow vs previous
            const prev = history[i + 1]; // next in array = previous in time
            let changeIcon = '';
            let changeColor = '#999';
            if (prev && prev.reading_type === r.reading_type) {
              const cur = r.reading_type === 'BLOOD_PRESSURE' ? parseFloat(r.systolic) : r.reading_type === 'BLOOD_GLUCOSE' ? parseFloat(r.glucose_level) : parseFloat(r.total_cholesterol);
              const pre = prev.reading_type === 'BLOOD_PRESSURE' ? parseFloat(prev.systolic) : prev.reading_type === 'BLOOD_GLUCOSE' ? parseFloat(prev.glucose_level) : parseFloat(prev.total_cholesterol);
              if (cur < pre) { changeIcon = '\u2193'; changeColor = '#16A34A'; }
              else if (cur > pre) { changeIcon = '\u2191'; changeColor = '#DC2626'; }
              else { changeIcon = '='; changeColor = '#2563EB'; }
            }

            // Classification
            let status = '';
            if (r.reading_type === 'BLOOD_PRESSURE') {
              const sys = parseFloat(r.systolic), dia = parseFloat(r.diastolic);
              status = sys < 120 && dia < 80 ? 'Normal' : sys < 130 ? 'Elevated' : sys < 140 || dia < 90 ? 'High (S1)' : 'High (S2)';
            } else if (r.reading_type === 'BLOOD_GLUCOSE') {
              const g = parseFloat(r.glucose_level);
              status = g < 100 ? 'Normal' : g < 126 ? 'Pre-diabetic' : 'Diabetic';
            } else if (r.reading_type === 'CHOLESTEROL') {
              const c = parseFloat(r.total_cholesterol);
              status = c < 200 ? 'Desirable' : c < 240 ? 'Borderline' : 'High';
            }

            const statusColor = status.includes('Normal') || status === 'Desirable' ? '#16A34A' : status.includes('High') || status.includes('Diabetic') ? '#DC2626' : '#E87722';

            return (
              <div key={r.id} style={s.tableRow}>
                <span>{new Date(r.recorded_at).toLocaleString()}</span>
                <span>{r.reading_type.replace(/_/g, ' ')}</span>
                <span style={{ fontWeight: 600 }}>
                  {r.reading_type === 'BLOOD_PRESSURE' && `${n(r.systolic)}/${n(r.diastolic)}`}
                  {r.reading_type === 'BLOOD_GLUCOSE' && `${n(r.glucose_level)}`}
                  {r.reading_type === 'CHOLESTEROL' && `${n(r.total_cholesterol)}`}
                  {changeIcon && <span style={{ marginLeft: 6, color: changeColor, fontWeight: 700 }}>{changeIcon}</span>}
                </span>
                <span style={{ color: statusColor, fontWeight: 600, fontSize: 12 }}>{status}</span>
                <span style={{ color: '#666' }}>{r.notes || '-'}</span>
              </div>
            );
          })}
          {history.length === 0 && <div style={{ padding: 30, textAlign: 'center', color: '#999' }}>No readings for this period</div>}
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

  // Trend cards
  trendGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 },
  trendCard: { backgroundColor: '#fff', borderRadius: 14, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' },
  trendHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  trendType: { fontSize: 12, fontWeight: 700, color: '#E87722', textTransform: 'uppercase', letterSpacing: 0.5 },
  trendBadge: { padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700, border: '1px solid', display: 'flex', alignItems: 'center', gap: 4 },
  trendValue: { fontSize: 38, fontWeight: 700, color: '#1A1A2E', marginTop: 4 },
  trendUnit: { fontSize: 13, color: '#999', marginTop: -2 },
  classification: { fontSize: 13, fontWeight: 700, marginTop: 6 },
  changeRow: { marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 },
  ctx: { fontSize: 12, color: '#666', marginTop: 4 },
  trendDate: { fontSize: 12, color: '#999', marginTop: 8 },
  readingCount: { fontSize: 11, color: '#bbb', marginTop: 2 },
  noData: { fontSize: 14, color: '#ccc', marginTop: 20, marginBottom: 10, textAlign: 'center' },

  // History section
  sectionTitle: { fontSize: 18, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  downloadBtn: { padding: '8px 18px', borderRadius: 8, border: '1px solid #1A1A2E', backgroundColor: '#fff', color: '#1A1A2E', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  filterRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 },
  filterGroup: { display: 'flex', gap: 6 },
  filterBtn: { padding: '6px 12px', borderRadius: 6, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 500 },
  dateFilters: { display: 'flex', alignItems: 'center', gap: 6 },
  dateLbl: { fontSize: 12, color: '#666', fontWeight: 600 },
  dateInput: { padding: '6px 10px', borderRadius: 6, border: '1px solid #ddd', fontSize: 13 },
  clearBtn: { padding: '6px 10px', borderRadius: 6, border: 'none', backgroundColor: '#eee', cursor: 'pointer', fontSize: 12, color: '#666' },

  // Table
  table: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  tableHead: { display: 'grid', gridTemplateColumns: '170px 130px 130px 100px 1fr', padding: '12px 18px', backgroundColor: '#F8F8FA', fontSize: 12, fontWeight: 600, color: '#666' },
  tableRow: { display: 'grid', gridTemplateColumns: '170px 130px 130px 100px 1fr', padding: '12px 18px', borderTop: '1px solid #f0f0f0', fontSize: 13, alignItems: 'center' },
};
