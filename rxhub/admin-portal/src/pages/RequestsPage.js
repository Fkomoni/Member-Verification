import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

const STATUS_COLORS = {
  PENDING: '#E87722',
  REVIEWED: '#2563EB',
  APPROVED: '#16A34A',
  REJECTED: '#DC2626',
  MODIFIED: '#7C3AED',
};

export default function RequestsPage() {
  const [requests, setRequests] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const page = parseInt(searchParams.get('page') || '1');
  const statusFilter = searchParams.get('status') || '';

  useEffect(() => {
    setLoading(true);
    const params = { page, page_size: 20 };
    if (statusFilter) params.status = statusFilter;

    api.get('/admin/requests', { params })
      .then(({ data }) => {
        setRequests(data.requests);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, statusFilter]);

  const setFilter = (status) => {
    const params = {};
    if (status) params.status = status;
    params.page = '1';
    setSearchParams(params);
  };

  return (
    <div>
      <h1 style={styles.heading}>Member Requests</h1>

      <div style={styles.filters}>
        {['', 'PENDING', 'APPROVED', 'REJECTED', 'MODIFIED'].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              ...styles.filterBtn,
              backgroundColor: statusFilter === s ? '#1A1A2E' : '#fff',
              color: statusFilter === s ? '#fff' : '#333',
            }}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div style={styles.table}>
            <div style={styles.headerRow}>
              <span style={styles.col}>Member ID</span>
              <span style={styles.col}>Type</span>
              <span style={styles.col}>Action</span>
              <span style={styles.col}>Status</span>
              <span style={styles.col}>Date</span>
            </div>
            {requests.map((req) => (
              <div
                key={req.id}
                style={styles.row}
                onClick={() => navigate(`/requests/${req.id}`)}
              >
                <span style={styles.col}>{req.member_id}</span>
                <span style={styles.col}>{req.request_type}</span>
                <span style={styles.col}>{req.action}</span>
                <span style={styles.col}>
                  <span style={{ ...styles.badge, backgroundColor: STATUS_COLORS[req.status] || '#999' }}>
                    {req.status}
                  </span>
                </span>
                <span style={styles.col}>{new Date(req.created_at).toLocaleDateString()}</span>
              </div>
            ))}
            {requests.length === 0 && <div style={styles.empty}>No requests found</div>}
          </div>

          <div style={styles.pagination}>
            <button
              disabled={page <= 1}
              onClick={() => setSearchParams({ ...Object.fromEntries(searchParams), page: String(page - 1) })}
              style={styles.pageBtn}
            >
              Previous
            </button>
            <span style={styles.pageInfo}>Page {page} of {Math.ceil(total / 20) || 1}</span>
            <button
              disabled={page * 20 >= total}
              onClick={() => setSearchParams({ ...Object.fromEntries(searchParams), page: String(page + 1) })}
              style={styles.pageBtn}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const styles = {
  heading: { fontSize: 28, fontWeight: 700, color: '#1A1A2E', margin: '0 0 24px' },
  filters: { display: 'flex', gap: 8, marginBottom: 24 },
  filterBtn: {
    padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd',
    cursor: 'pointer', fontSize: 13, fontWeight: 500,
  },
  table: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  headerRow: {
    display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 120px 100px',
    padding: '14px 20px', backgroundColor: '#F8F8FA', fontWeight: 600, fontSize: 13, color: '#666',
  },
  row: {
    display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 120px 100px',
    padding: '14px 20px', borderTop: '1px solid #f0f0f0', cursor: 'pointer',
    fontSize: 14, transition: 'background 0.15s',
  },
  col: { display: 'flex', alignItems: 'center' },
  badge: { padding: '4px 10px', borderRadius: 12, color: '#fff', fontSize: 11, fontWeight: 600 },
  empty: { padding: 40, textAlign: 'center', color: '#999' },
  pagination: { display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 24 },
  pageBtn: {
    padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd',
    backgroundColor: '#fff', cursor: 'pointer', fontSize: 13,
  },
  pageInfo: { fontSize: 13, color: '#666' },
};
