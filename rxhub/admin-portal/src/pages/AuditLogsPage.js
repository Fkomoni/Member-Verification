import React, { useState, useEffect } from 'react';
import api from '../services/api';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get('/admin/audit-logs', { params: { page, page_size: 30 } })
      .then(({ data }) => {
        setLogs(data.logs);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div>
      <h1 style={styles.heading}>Audit Logs</h1>
      <p style={styles.subtext}>Complete audit trail of all request actions</p>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <>
          <div style={styles.table}>
            <div style={styles.headerRow}>
              <span style={styles.col}>Time</span>
              <span style={styles.col}>Actor</span>
              <span style={styles.col}>Action</span>
              <span style={styles.col}>Request ID</span>
              <span style={styles.col}>Notes</span>
            </div>
            {logs.map((log) => (
              <div key={log.id} style={styles.row}>
                <span style={styles.col}>{new Date(log.created_at).toLocaleString()}</span>
                <span style={styles.col}>
                  <span style={styles.actorBadge}>{log.actor_type}</span>
                  <span style={{ marginLeft: 6, fontSize: 12 }}>{log.actor_id?.slice(0, 8)}...</span>
                </span>
                <span style={styles.col}><strong>{log.action}</strong></span>
                <span style={{ ...styles.col, fontSize: 12, fontFamily: 'monospace' }}>
                  {log.request_id?.slice(0, 8)}...
                </span>
                <span style={styles.col}>{log.notes || '-'}</span>
              </div>
            ))}
            {logs.length === 0 && <div style={styles.empty}>No audit logs found</div>}
          </div>

          <div style={styles.pagination}>
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} style={styles.pageBtn}>Previous</button>
            <span style={styles.pageInfo}>Page {page} of {Math.ceil(total / 30) || 1}</span>
            <button disabled={page * 30 >= total} onClick={() => setPage(page + 1)} style={styles.pageBtn}>Next</button>
          </div>
        </>
      )}
    </div>
  );
}

const styles = {
  heading: { fontSize: 28, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  subtext: { color: '#666', marginTop: 4, marginBottom: 24 },
  table: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.08)' },
  headerRow: {
    display: 'grid', gridTemplateColumns: '160px 180px 120px 140px 1fr',
    padding: '14px 20px', backgroundColor: '#F8F8FA', fontWeight: 600, fontSize: 13, color: '#666',
  },
  row: {
    display: 'grid', gridTemplateColumns: '160px 180px 120px 140px 1fr',
    padding: '12px 20px', borderTop: '1px solid #f0f0f0', fontSize: 13,
  },
  col: { display: 'flex', alignItems: 'center' },
  actorBadge: {
    padding: '2px 8px', borderRadius: 4, backgroundColor: '#1A1A2E',
    color: '#fff', fontSize: 10, fontWeight: 600,
  },
  empty: { padding: 40, textAlign: 'center', color: '#999' },
  pagination: { display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 16, marginTop: 24 },
  pageBtn: {
    padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd',
    backgroundColor: '#fff', cursor: 'pointer', fontSize: 13,
  },
  pageInfo: { fontSize: 13, color: '#666' },
};
