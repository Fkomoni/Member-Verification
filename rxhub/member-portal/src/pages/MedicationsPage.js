import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function MedicationsPage() {
  const [meds, setMeds] = useState([]);

  useEffect(() => { api.get('/member/medications').then(r => setMeds(r.data)).catch(() => {}); }, []);

  const requestRefill = async (med) => {
    try {
      await api.post('/refill/request', { medication_id: med.id, comment: 'Refill requested from portal' });
      alert('Refill request submitted for ' + med.drug_name);
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  return (
    <div>
      <h1 style={s.heading}>My Medications</h1>
      <p style={s.sub}>Your current medication list synced from your PBM plan</p>

      <div style={s.grid}>
        {meds.map(m => (
          <div key={m.id} style={s.card}>
            <div style={s.cardHead}>
              <div>
                <div style={s.drug}>{m.drug_name}</div>
                {m.generic_name && <div style={s.generic}>{m.generic_name}</div>}
              </div>
              <span style={{ ...s.badge, backgroundColor: m.status === 'ACTIVE' ? '#16A34A' : '#999' }}>{m.status}</span>
            </div>

            <div style={s.detailGrid}>
              <Detail label="Dosage" value={m.dosage} />
              <Detail label="Frequency" value={m.frequency} />
              <Detail label="Refills Used" value={`${m.refill_count} / ${m.max_refills}`} />
              <Detail label="Days Supply" value={`${m.days_supply} days`} />
            </div>

            {m.days_until_runout != null && (
              <div style={{ ...s.runout, borderLeftColor: m.days_until_runout <= 7 ? '#C8102E' : '#E87722', backgroundColor: m.days_until_runout <= 7 ? '#FEE2E2' : '#FFF7ED' }}>
                {m.days_until_runout <= 0 ? 'Supply depleted — request refill now' : `${m.days_until_runout} days of supply remaining`}
              </div>
            )}

            {m.is_covered && (
              <div style={s.coverage}>Coverage: {parseFloat(m.coverage_pct)}% &middot; Copay: &#8358;{parseFloat(m.copay_amount).toLocaleString()}</div>
            )}

            <button style={s.refillBtn} onClick={() => requestRefill(m)}>Request Refill</button>
          </div>
        ))}
        {meds.length === 0 && <p style={{ color: '#999' }}>No medications found</p>}
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return <div><div style={{ fontSize: 11, color: '#999', fontWeight: 600 }}>{label}</div><div style={{ fontSize: 14, color: '#333', marginTop: 2 }}>{value}</div></div>;
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 24, fontSize: 14 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 22, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  drug: { fontSize: 17, fontWeight: 700, color: '#1A1A2E' },
  generic: { fontSize: 13, color: '#666' },
  badge: { padding: '3px 10px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600, flexShrink: 0 },
  detailGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 },
  runout: { borderLeft: '4px solid', borderRadius: 6, padding: '8px 12px', marginTop: 12, fontSize: 13, fontWeight: 500 },
  coverage: { fontSize: 12, color: '#16A34A', marginTop: 8 },
  refillBtn: { marginTop: 14, width: '100%', padding: '10px', borderRadius: 8, border: 'none', backgroundColor: '#1A1A2E', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
};
