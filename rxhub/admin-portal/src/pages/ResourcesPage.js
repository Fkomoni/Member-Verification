import React, { useState, useEffect } from 'react';
import api from '../services/api';

const CATEGORIES = ['NEWSLETTER', 'HEALTH_TIP', 'DRUG_ALERT', 'SCARCITY_ALERT', 'PBM_UPDATE'];

export default function ResourcesPage() {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ title: '', body: '', category: 'NEWSLETTER', diagnosis_tags: '', is_published: false });
  const [saving, setSaving] = useState(false);

  const fetchResources = () => {
    setLoading(true);
    api.get('/resources', { params: { page_size: 50 } })
      .then(({ data }) => setResources(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchResources(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/resources/admin', {
        ...form,
        diagnosis_tags: form.diagnosis_tags ? form.diagnosis_tags.split(',').map(t => t.trim()) : [],
      });
      setShowForm(false);
      setForm({ title: '', body: '', category: 'NEWSLETTER', diagnosis_tags: '', is_published: false });
      fetchResources();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create resource');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div style={styles.headerRow}>
        <div>
          <h1 style={styles.heading}>Resources</h1>
          <p style={styles.subtext}>Manage newsletters, health tips, and drug alerts</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={styles.addBtn}>
          {showForm ? 'Cancel' : '+ New Resource'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} style={styles.form}>
          <input
            placeholder="Title" required value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            style={styles.input}
          />
          <textarea
            placeholder="Body content..." required value={form.body}
            onChange={(e) => setForm({ ...form, body: e.target.value })}
            style={{ ...styles.input, minHeight: 120, resize: 'vertical' }}
          />
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            style={styles.input}
          >
            {CATEGORIES.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
          </select>
          <input
            placeholder="Diagnosis tags (comma-separated)" value={form.diagnosis_tags}
            onChange={(e) => setForm({ ...form, diagnosis_tags: e.target.value })}
            style={styles.input}
          />
          <label style={styles.checkLabel}>
            <input
              type="checkbox" checked={form.is_published}
              onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
            />
            Publish immediately
          </label>
          <button type="submit" disabled={saving} style={styles.submitBtn}>
            {saving ? 'Creating...' : 'Create Resource'}
          </button>
        </form>
      )}

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div style={styles.grid}>
          {resources.map((r) => (
            <div key={r.id} style={styles.card}>
              <div style={styles.cardCategory}>{r.category.replace(/_/g, ' ')}</div>
              <h3 style={styles.cardTitle}>{r.title}</h3>
              <p style={styles.cardBody}>{r.body.slice(0, 120)}...</p>
              {r.diagnosis_tags?.length > 0 && (
                <div style={styles.tags}>
                  {r.diagnosis_tags.map(t => <span key={t} style={styles.tag}>{t}</span>)}
                </div>
              )}
              <div style={styles.cardDate}>{r.published_at ? new Date(r.published_at).toLocaleDateString() : 'Draft'}</div>
            </div>
          ))}
          {resources.length === 0 && <p style={{ color: '#999' }}>No resources yet</p>}
        </div>
      )}
    </div>
  );
}

const styles = {
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 },
  heading: { fontSize: 28, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  subtext: { color: '#666', marginTop: 4 },
  addBtn: {
    padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E',
    color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
  },
  form: {
    backgroundColor: '#fff', borderRadius: 12, padding: 24, marginBottom: 24,
    display: 'flex', flexDirection: 'column', gap: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  input: { padding: '12px 16px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14 },
  checkLabel: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 },
  submitBtn: {
    padding: '12px', borderRadius: 8, border: 'none', backgroundColor: '#1A1A2E',
    color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
  },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  cardCategory: { fontSize: 11, fontWeight: 700, color: '#E87722', textTransform: 'uppercase', marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: 700, color: '#1A1A2E', margin: '0 0 8px' },
  cardBody: { fontSize: 13, color: '#666', lineHeight: 1.5, margin: '0 0 12px' },
  tags: { display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 },
  tag: { padding: '2px 8px', backgroundColor: '#F0F0F0', borderRadius: 4, fontSize: 11, color: '#444' },
  cardDate: { fontSize: 12, color: '#999' },
};
