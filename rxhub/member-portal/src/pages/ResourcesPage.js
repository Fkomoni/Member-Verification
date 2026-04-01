import React, { useState, useEffect } from 'react';
import api from '../services/api';

const CATS = ['', 'NEWSLETTER', 'HEALTH_TIP', 'DRUG_ALERT', 'SCARCITY_ALERT', 'PBM_UPDATE'];

export default function ResourcesPage() {
  const [resources, setResources] = useState([]);
  const [cat, setCat] = useState('');

  useEffect(() => {
    const params = { page_size: 30 };
    if (cat) params.category = cat;
    api.get('/resources', { params }).then(r => setResources(r.data)).catch(() => {});
  }, [cat]);

  return (
    <div>
      <h1 style={s.heading}>Resource Center</h1>
      <p style={s.sub}>Health tips, drug alerts, and newsletters</p>

      <div style={s.filters}>
        {CATS.map(c => (
          <button key={c} onClick={() => setCat(c)} style={{ ...s.filterBtn, ...(cat === c ? { backgroundColor: '#1A1A2E', color: '#fff' } : {}) }}>
            {c ? c.replace(/_/g, ' ') : 'All'}
          </button>
        ))}
      </div>

      <div style={s.grid}>
        {resources.map(r => (
          <div key={r.id} style={s.card}>
            <div style={s.cardCat}>{r.category.replace(/_/g, ' ')}</div>
            <h3 style={s.cardTitle}>{r.title}</h3>
            <p style={s.cardBody}>{r.body}</p>
            {r.diagnosis_tags?.length > 0 && (
              <div style={s.tags}>{r.diagnosis_tags.map(t => <span key={t} style={s.tag}>{t}</span>)}</div>
            )}
            <div style={s.cardDate}>{r.published_at ? new Date(r.published_at).toLocaleDateString() : ''}</div>
          </div>
        ))}
        {resources.length === 0 && <p style={{ color: '#999' }}>No resources found</p>}
      </div>
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 20, fontSize: 14 },
  filters: { display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' },
  filterBtn: { padding: '7px 14px', borderRadius: 6, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 500 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 22, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  cardCat: { fontSize: 11, fontWeight: 700, color: '#E87722', textTransform: 'uppercase' },
  cardTitle: { fontSize: 16, fontWeight: 700, color: '#1A1A2E', margin: '4px 0 8px' },
  cardBody: { fontSize: 14, color: '#555', lineHeight: 1.6 },
  tags: { display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 10 },
  tag: { padding: '2px 8px', backgroundColor: '#F0F0F0', borderRadius: 4, fontSize: 11, color: '#444' },
  cardDate: { fontSize: 12, color: '#999', marginTop: 8 },
};
