import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function RequestDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [request, setRequest] = useState(null);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');

  useEffect(() => {
    api.get(`/admin/requests/${id}`)
      .then(({ data }) => setRequest(data))
      .catch(() => navigate('/requests'))
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleAction = async (action) => {
    setActionLoading(action);
    try {
      await api.post(`/admin/requests/${id}/${action.toLowerCase()}`, {
        action: action.toUpperCase(),
        comment,
      });
      const { data } = await api.get(`/admin/requests/${id}`);
      setRequest(data);
      setComment('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading('');
    }
  };

  if (loading) return <p>Loading...</p>;
  if (!request) return <p>Request not found</p>;

  const isPending = request.status === 'PENDING' || request.status === 'REVIEWED';

  return (
    <div>
      <button onClick={() => navigate('/requests')} style={styles.backBtn}>Back to Requests</button>

      <div style={styles.card}>
        <div style={styles.header}>
          <h2 style={styles.title}>Request Detail</h2>
          <span style={{ ...styles.badge, backgroundColor: statusColor(request.status) }}>
            {request.status}
          </span>
        </div>

        <div style={styles.grid}>
          <Field label="Request ID" value={request.id} />
          <Field label="Member ID" value={request.member_id} />
          <Field label="Type" value={request.request_type} />
          <Field label="Action" value={request.action} />
          <Field label="Created" value={new Date(request.created_at).toLocaleString()} />
          {request.resolved_at && <Field label="Resolved" value={new Date(request.resolved_at).toLocaleString()} />}
        </div>

        {request.comment && (
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Member Comment</h3>
            <p style={styles.text}>{request.comment}</p>
          </div>
        )}

        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Payload</h3>
          <pre style={styles.json}>{JSON.stringify(request.payload, null, 2)}</pre>
        </div>

        {request.attachment_url && (
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Attachment</h3>
            <a href={request.attachment_url} target="_blank" rel="noopener noreferrer" style={styles.link}>
              View Prescription
            </a>
          </div>
        )}

        {request.admin_comment && (
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Admin Comment</h3>
            <p style={styles.text}>{request.admin_comment}</p>
          </div>
        )}

        {isPending && (
          <div style={styles.actions}>
            <h3 style={styles.sectionTitle}>Take Action</h3>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add a comment (optional)..."
              style={styles.textarea}
            />
            <div style={styles.btnGroup}>
              <button
                onClick={() => handleAction('approve')}
                disabled={!!actionLoading}
                style={{ ...styles.actionBtn, backgroundColor: '#16A34A' }}
              >
                {actionLoading === 'approve' ? 'Approving...' : 'Approve'}
              </button>
              <button
                onClick={() => handleAction('reject')}
                disabled={!!actionLoading}
                style={{ ...styles.actionBtn, backgroundColor: '#DC2626' }}
              >
                {actionLoading === 'reject' ? 'Rejecting...' : 'Reject'}
              </button>
              <button
                onClick={() => handleAction('modify')}
                disabled={!!actionLoading}
                style={{ ...styles.actionBtn, backgroundColor: '#7C3AED' }}
              >
                {actionLoading === 'modify' ? 'Modifying...' : 'Modify'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 12, color: '#666', fontWeight: 600 }}>{label}</div>
      <div style={{ fontSize: 14, color: '#1A1A2E', marginTop: 2 }}>{value}</div>
    </div>
  );
}

function statusColor(s) {
  const map = { PENDING: '#E87722', APPROVED: '#16A34A', REJECTED: '#DC2626', MODIFIED: '#7C3AED', REVIEWED: '#2563EB' };
  return map[s] || '#999';
}

const styles = {
  backBtn: {
    background: 'none', border: 'none', color: '#C8102E', cursor: 'pointer',
    fontSize: 14, fontWeight: 600, marginBottom: 20, padding: 0,
  },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 32, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  title: { fontSize: 22, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  badge: { padding: '6px 14px', borderRadius: 12, color: '#fff', fontSize: 12, fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 20, marginBottom: 24 },
  section: { marginTop: 24, paddingTop: 24, borderTop: '1px solid #f0f0f0' },
  sectionTitle: { fontSize: 14, fontWeight: 700, color: '#1A1A2E', margin: '0 0 8px' },
  text: { fontSize: 14, color: '#444', lineHeight: 1.6, margin: 0 },
  json: { backgroundColor: '#F8F8FA', padding: 16, borderRadius: 8, fontSize: 12, overflow: 'auto', maxHeight: 300 },
  link: { color: '#C8102E', fontWeight: 600, fontSize: 14 },
  actions: { marginTop: 32, paddingTop: 24, borderTop: '2px solid #f0f0f0' },
  textarea: {
    width: '100%', minHeight: 80, padding: '12px 16px', borderRadius: 8,
    border: '1px solid #ddd', fontSize: 14, resize: 'vertical', marginBottom: 16,
    boxSizing: 'border-box',
  },
  btnGroup: { display: 'flex', gap: 12 },
  actionBtn: {
    padding: '12px 24px', borderRadius: 8, border: 'none', color: '#fff',
    fontSize: 14, fontWeight: 600, cursor: 'pointer',
  },
};
