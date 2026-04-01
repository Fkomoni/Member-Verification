import React, { useState, useEffect } from 'react';
import api from '../services/api';

const CATS = ['', 'NEWSLETTER', 'HEALTH_TIP', 'DRUG_ALERT', 'SCARCITY_ALERT', 'PBM_UPDATE'];

const CAT_COLORS = {
  NEWSLETTER: '#2563EB',
  HEALTH_TIP: '#16A34A',
  DRUG_ALERT: '#DC2626',
  SCARCITY_ALERT: '#E87722',
  PBM_UPDATE: '#7C3AED',
};

export default function ResourcesPage() {
  const [resources, setResources] = useState([]);
  const [cat, setCat] = useState('');

  useEffect(() => {
    const params = { page_size: 30 };
    if (cat) params.category = cat;
    api.get('/resources', { params }).then(r => setResources(r.data)).catch(() => {});
  }, [cat]);

  const openNewsletter = (r) => {
    // If thumbnail_url points to a newsletter HTML file, open it in new tab
    if (r.thumbnail_url && r.thumbnail_url.startsWith('/newsletters/')) {
      window.open(r.thumbnail_url, '_blank');
    }
  };

  return (
    <div>
      <h1 style={s.heading}>Resource Center</h1>
      <p style={s.sub}>Health newsletters, drug alerts, and scarcity notices</p>

      <div style={s.filters}>
        {CATS.map(c => (
          <button key={c} onClick={() => setCat(c)} style={{ ...s.filterBtn, ...(cat === c ? { backgroundColor: '#262626', color: '#fff' } : {}) }}>
            {c ? c.replace(/_/g, ' ') : 'All'}
          </button>
        ))}
      </div>

      <div style={s.grid}>
        {resources.map(r => {
          const isNewsletter = r.category === 'NEWSLETTER' && r.thumbnail_url;
          const catColor = CAT_COLORS[r.category] || '#666';

          return (
            <div key={r.id} style={{ ...s.card, cursor: isNewsletter ? 'pointer' : 'default' }}
              onClick={() => isNewsletter && openNewsletter(r)}>
              <div style={{ ...s.cardCat, color: catColor }}>{r.category.replace(/_/g, ' ')}</div>
              <h3 style={s.cardTitle}>{r.title}</h3>
              <p style={s.cardBody}>{r.body.length > 250 ? r.body.slice(0, 250) + '...' : r.body}</p>
              {r.diagnosis_tags?.length > 0 && (
                <div style={s.tags}>{r.diagnosis_tags.map(t => <span key={t} style={s.tag}>{t}</span>)}</div>
              )}
              <div style={s.cardFooter}>
                <span style={s.cardDate}>{r.published_at ? new Date(r.published_at).toLocaleDateString() : ''}</span>
                {isNewsletter && <span style={s.readMore}>Read Full Newsletter &rarr;</span>}
              </div>
            </div>
          );
        })}
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
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 22, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', transition: 'box-shadow 0.2s' },
  cardCat: { fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 },
  cardTitle: { fontSize: 16, fontWeight: 700, color: '#1A1A2E', margin: '6px 0 8px' },
  cardBody: { fontSize: 14, color: '#555', lineHeight: 1.6, whiteSpace: 'pre-line' },
  tags: { display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 },
  tag: { padding: '2px 8px', backgroundColor: '#F0F0F0', borderRadius: 4, fontSize: 11, color: '#444' },
  cardFooter: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 },
  cardDate: { fontSize: 12, color: '#999' },
  readMore: { fontSize: 13, color: '#C8102E', fontWeight: 600 },
};
