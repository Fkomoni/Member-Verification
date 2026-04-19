import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';

const STATUS_COLORS = {
  PENDING: '#E87722', REVIEWED: '#2563EB', APPROVED: '#16A34A',
  REJECTED: '#DC2626', MODIFIED: '#7C3AED',
};

export default function RequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [expandedMember, setExpandedMember] = useState(null);
  const [comment, setComment] = useState('');
  const [actionLoading, setActionLoading] = useState('');

  const statusFilter = searchParams.get('status') || '';

  const fetchRequests = () => {
    setLoading(true);
    const params = { page_size: 200 };
    if (statusFilter) params.status = statusFilter;
    api.get('/admin/requests', { params })
      .then(({ data }) => setRequests(data.requests))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRequests(); }, [statusFilter]);

  // Group requests by member
  const grouped = {};
  requests.forEach(r => {
    if (!grouped[r.member_id]) grouped[r.member_id] = [];
    grouped[r.member_id].push(r);
  });

  const pendingCount = (memberId) => grouped[memberId].filter(r => r.status === 'PENDING').length;

  const handleAction = async (requestId, action) => {
    setActionLoading(`${requestId}-${action}`);
    try {
      await api.post(`/admin/requests/${requestId}/${action.toLowerCase()}`, {
        action: action.toUpperCase(),
        comment: comment || undefined,
      });
      setComment('');
      fetchRequests();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    } finally {
      setActionLoading('');
    }
  };

  const handleBulkAction = async (memberId, action) => {
    const pending = grouped[memberId].filter(r => r.status === 'PENDING');
    if (!pending.length) return;
    const confirmMsg = `${action} all ${pending.length} pending request(s) for ${memberId}?`;
    if (!window.confirm(confirmMsg)) return;

    setActionLoading(`bulk-${memberId}-${action}`);
    for (const req of pending) {
      try {
        await api.post(`/admin/requests/${req.id}/${action.toLowerCase()}`, {
          action: action.toUpperCase(),
          comment: comment || `Bulk ${action.toLowerCase()} by admin`,
        });
      } catch {}
    }
    setComment('');
    setActionLoading('');
    fetchRequests();
  };

  return (
    <div>
      <h1 style={s.heading}>Member Requests</h1>
      <p style={s.sub}>{requests.length} request(s) from {Object.keys(grouped).length} member(s)</p>

      <div style={s.filters}>
        {['', 'PENDING', 'APPROVED', 'REJECTED', 'MODIFIED'].map(st => (
          <button key={st} onClick={() => { setSearchParams(st ? { status: st } : {}); setExpandedMember(null); }}
            style={{ ...s.filterBtn, backgroundColor: statusFilter === st ? '#262626' : '#fff', color: statusFilter === st ? '#fff' : '#333' }}>
            {st || 'All'}
          </button>
        ))}
      </div>

      {loading ? <p>Loading...</p> : (
        <div style={s.memberList}>
          {Object.entries(grouped).map(([memberId, memberRequests]) => {
            const isExpanded = expandedMember === memberId;
            const pending = memberRequests.filter(r => r.status === 'PENDING').length;

            return (
              <div key={memberId} style={s.memberCard}>
                {/* Member Header Row */}
                <div style={s.memberHeader} onClick={() => setExpandedMember(isExpanded ? null : memberId)}>
                  <div style={s.memberInfo}>
                    <div style={s.memberId}>{memberId}</div>
                    <div style={s.memberMeta}>
                      {memberRequests.length} request(s)
                      {pending > 0 && <span style={s.pendingBadge}>{pending} pending</span>}
                    </div>
                  </div>
                  <div style={s.memberSummary}>
                    {memberRequests.slice(0, 3).map(r => (
                      <span key={r.id} style={{ ...s.miniTag, backgroundColor: STATUS_COLORS[r.status] + '20', color: STATUS_COLORS[r.status] }}>
                        {r.action}
                      </span>
                    ))}
                    {memberRequests.length > 3 && <span style={s.moreTag}>+{memberRequests.length - 3}</span>}
                  </div>
                  <div style={s.expandIcon}>{isExpanded ? '\u25B2' : '\u25BC'}</div>
                </div>

                {/* Expanded: All requests for this member */}
                {isExpanded && (
                  <div style={s.expandedPanel}>
                    {/* Bulk actions */}
                    {pending > 0 && (
                      <div style={s.bulkActions}>
                        <span style={s.bulkLabel}>Bulk actions for all {pending} pending:</span>
                        <button style={s.approveAllBtn} onClick={() => handleBulkAction(memberId, 'approve')}
                          disabled={!!actionLoading}>Approve All</button>
                        <button style={s.rejectAllBtn} onClick={() => handleBulkAction(memberId, 'reject')}
                          disabled={!!actionLoading}>Reject All</button>
                      </div>
                    )}

                    {/* Individual requests */}
                    {memberRequests.map(req => (
                      <div key={req.id} style={s.requestCard}>
                        <div style={s.requestHeader}>
                          <div>
                            <span style={s.requestType}>{req.request_type.replace(/_/g, ' ')}</span>
                            <span style={s.requestAction}>{req.action}</span>
                          </div>
                          <div style={s.requestRight}>
                            <span style={{ ...s.badge, backgroundColor: STATUS_COLORS[req.status] }}>{req.status}</span>
                            <span style={s.requestDate}>{new Date(req.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        {/* Payload */}
                        <div style={s.payload}>
                          {Object.entries(req.payload || {}).map(([k, v]) => (
                            <div key={k} style={s.payloadRow}>
                              <span style={s.payloadKey}>{k.replace(/_/g, ' ')}:</span>
                              <span style={s.payloadVal}>{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                            </div>
                          ))}
                        </div>

                        {req.comment && <div style={s.memberComment}>Member: "{req.comment}"</div>}

                        {req.attachment_url && (
                          <a href={req.attachment_url} target="_blank" rel="noopener noreferrer" style={s.attachment}>
                            View Attachment
                          </a>
                        )}

                        {req.admin_comment && (
                          <div style={s.adminComment}>Admin: "{req.admin_comment}"</div>
                        )}

                        {/* Action buttons for pending requests */}
                        {(req.status === 'PENDING' || req.status === 'REVIEWED') && (
                          <div style={s.actions}>
                            <input style={s.commentInput} placeholder="Add comment (optional)..."
                              value={comment} onChange={e => setComment(e.target.value)} />
                            <div style={s.actionBtns}>
                              <button style={s.approveBtn} onClick={() => handleAction(req.id, 'approve')}
                                disabled={actionLoading === `${req.id}-approve`}>
                                {actionLoading === `${req.id}-approve` ? '...' : 'Approve'}
                              </button>
                              <button style={s.rejectBtn} onClick={() => handleAction(req.id, 'reject')}
                                disabled={actionLoading === `${req.id}-reject`}>
                                {actionLoading === `${req.id}-reject` ? '...' : 'Reject'}
                              </button>
                              <button style={s.modifyBtn} onClick={() => handleAction(req.id, 'modify')}
                                disabled={actionLoading === `${req.id}-modify`}>
                                {actionLoading === `${req.id}-modify` ? '...' : 'Modify'}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {Object.keys(grouped).length === 0 && <div style={s.empty}>No requests found</div>}
        </div>
      )}
    </div>
  );
}

const s = {
  heading: { fontSize: 28, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 20, fontSize: 14 },
  filters: { display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' },
  filterBtn: { padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd', cursor: 'pointer', fontSize: 13, fontWeight: 500 },

  memberList: { display: 'flex', flexDirection: 'column', gap: 12 },
  memberCard: { backgroundColor: '#fff', borderRadius: 12, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  memberHeader: { display: 'flex', alignItems: 'center', padding: '16px 20px', cursor: 'pointer', gap: 16, transition: 'background 0.15s' },
  memberInfo: { flex: 1 },
  memberId: { fontSize: 16, fontWeight: 700, color: '#1A1A2E' },
  memberMeta: { fontSize: 13, color: '#666', marginTop: 2, display: 'flex', alignItems: 'center', gap: 8 },
  pendingBadge: { backgroundColor: '#FFF7ED', color: '#E87722', padding: '2px 8px', borderRadius: 10, fontSize: 11, fontWeight: 700 },
  memberSummary: { display: 'flex', gap: 4, flexWrap: 'wrap' },
  miniTag: { padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 600 },
  moreTag: { padding: '3px 8px', borderRadius: 6, fontSize: 11, color: '#999', backgroundColor: '#f0f0f0' },
  expandIcon: { fontSize: 12, color: '#999', flexShrink: 0 },

  expandedPanel: { padding: '0 20px 20px', borderTop: '1px solid #f0f0f0' },
  bulkActions: { display: 'flex', alignItems: 'center', gap: 10, padding: '14px 0', borderBottom: '1px solid #f0f0f0', marginBottom: 12 },
  bulkLabel: { fontSize: 13, color: '#666', flex: 1 },
  approveAllBtn: { padding: '8px 16px', borderRadius: 6, border: 'none', backgroundColor: '#16A34A', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' },
  rejectAllBtn: { padding: '8px 16px', borderRadius: 6, border: 'none', backgroundColor: '#DC2626', color: '#fff', fontSize: 12, fontWeight: 600, cursor: 'pointer' },

  requestCard: { padding: '16px', backgroundColor: '#FAFAFA', borderRadius: 10, marginBottom: 10, border: '1px solid #f0f0f0' },
  requestHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  requestType: { fontSize: 11, fontWeight: 700, color: '#666', textTransform: 'uppercase', letterSpacing: 0.5 },
  requestAction: { fontSize: 14, fontWeight: 700, color: '#1A1A2E', marginLeft: 8 },
  requestRight: { display: 'flex', alignItems: 'center', gap: 10 },
  badge: { padding: '3px 10px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600 },
  requestDate: { fontSize: 12, color: '#999' },

  payload: { marginBottom: 8 },
  payloadRow: { display: 'flex', gap: 8, fontSize: 13, padding: '3px 0' },
  payloadKey: { color: '#999', fontWeight: 600, textTransform: 'capitalize', minWidth: 100 },
  payloadVal: { color: '#333' },

  memberComment: { fontSize: 13, color: '#555', fontStyle: 'italic', padding: '8px 12px', backgroundColor: '#FFF7ED', borderRadius: 6, marginBottom: 8 },
  adminComment: { fontSize: 13, color: '#16A34A', fontStyle: 'italic', padding: '8px 12px', backgroundColor: '#F0FDF4', borderRadius: 6, marginBottom: 8 },
  attachment: { fontSize: 13, color: '#C8102E', fontWeight: 600, display: 'inline-block', marginBottom: 8 },

  actions: { marginTop: 10, paddingTop: 10, borderTop: '1px solid #eee' },
  commentInput: { width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 13, marginBottom: 10, boxSizing: 'border-box' },
  actionBtns: { display: 'flex', gap: 8 },
  approveBtn: { padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#16A34A', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  rejectBtn: { padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#DC2626', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  modifyBtn: { padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#7C3AED', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },

  empty: { padding: 40, textAlign: 'center', color: '#999', backgroundColor: '#fff', borderRadius: 12 },
};
