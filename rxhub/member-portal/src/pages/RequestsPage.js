import React, { useState, useEffect } from 'react';
import api from '../services/api';

const STATUS_COLORS = { PENDING: '#E87722', APPROVED: '#16A34A', REJECTED: '#DC2626', MODIFIED: '#7C3AED', REVIEWED: '#2563EB' };

export default function RequestsPage() {
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    api.get('/requests/my', { params: { page_size: 50 } }).then(r => { setRequests(r.data.requests); setTotal(r.data.total); }).catch(() => {});
  }, []);

  return (
    <div>
      <h1 style={s.heading}>My Requests</h1>
      <p style={s.sub}>{total} total request(s)</p>

      <div style={s.table}>
        <div style={s.head}><span>Date</span><span>Type</span><span>Action</span><span>Status</span><span>Comment</span></div>
        {requests.map(r => (
          <div key={r.id} style={s.row}>
            <span>{new Date(r.created_at).toLocaleDateString()}</span>
            <span>{r.request_type.replace(/_/g, ' ')}</span>
            <span>{r.action}</span>
            <span><span style={{ ...s.badge, backgroundColor: STATUS_COLORS[r.status] || '#999' }}>{r.status}</span></span>
            <span style={{ color: '#666' }}>{r.comment || '-'}</span>
          </div>
        ))}
        {requests.length === 0 && <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>No requests yet</div>}
      </div>

      {requests.filter(r => r.admin_comment).length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: '#1A1A2E', marginBottom: 12 }}>Admin Responses</h2>
          {requests.filter(r => r.admin_comment).map(r => (
            <div key={r.id} style={s.response}>
              <strong>{r.request_type.replace(/_/g, ' ')} / {r.action}</strong>
              <span style={{ ...s.badge, backgroundColor: STATUS_COLORS[r.status] || '#999', marginLeft: 8 }}>{r.status}</span>
              <p style={{ margin: '8px 0 0', color: '#333', fontSize: 14 }}>{r.admin_comment}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 24, fontSize: 14 },
  table: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  head: { display: 'grid', gridTemplateColumns: '100px 140px 100px 100px 1fr', padding: '12px 18px', backgroundColor: '#F8F8FA', fontSize: 12, fontWeight: 600, color: '#666' },
  row: { display: 'grid', gridTemplateColumns: '100px 140px 100px 100px 1fr', padding: '12px 18px', borderTop: '1px solid #f0f0f0', fontSize: 13, alignItems: 'center' },
  badge: { padding: '3px 10px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600 },
  response: { backgroundColor: '#F0FDF4', borderRadius: 10, padding: 16, marginBottom: 10, fontSize: 14 },
};
