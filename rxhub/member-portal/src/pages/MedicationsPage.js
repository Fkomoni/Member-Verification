import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function MedicationsPage() {
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingMed, setEditingMed] = useState(null);
  const [editDosage, setEditDosage] = useState('');
  const [editQty, setEditQty] = useState('');
  const [editComment, setEditComment] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const navigate = useNavigate();

  const fetchMeds = () => api.get('/member/medications').then(r => setMeds(r.data)).catch(() => {});
  useEffect(() => { fetchMeds(); }, []);

  const deleteMedication = async (med) => {
    const reason = prompt(`Why do you want to delete ${med.drug_name}?\n\nThis will permanently remove it from your medication list.`);
    if (!reason) return;
    try {
      await api.post('/member/medications/delete-with-reason', { medication_id: med.id, comment: reason });
      setMeds(prev => prev.filter(m => m.id !== med.id));
      alert(`${med.drug_name} has been deleted from your list of medications.`);
    } catch (err) { alert(err.response?.data?.detail || 'Failed to delete'); }
  };

  const requestRefill = async (med) => {
    try {
      await api.post('/refill/request', { medication_id: med.id, comment: 'Refill requested from portal' });
      alert('Refill request submitted for ' + med.drug_name);
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  const requestAllRefills = async () => {
    setLoading(true);
    const activeMeds = meds.filter(m => m.status === 'ACTIVE');
    let success = 0;
    for (const med of activeMeds) {
      try {
        await api.post('/refill/request', { medication_id: med.id, comment: 'Bulk refill request — all medications' });
        success++;
      } catch {}
    }
    setLoading(false);
    alert(`Refill requested for ${success} of ${activeMeds.length} medications`);
  };

  const startEdit = (med) => {
    setEditingMed(med.id);
    setEditDosage(med.dosage !== 'N/A' ? med.dosage : '');
    setEditQty('');
    setEditComment('');
  };

  const cancelEdit = () => {
    setEditingMed(null);
    setEditDosage('');
    setEditQty('');
    setEditComment('');
  };

  const saveEdit = async (med) => {
    if (!editDosage && !editQty) return alert('Please enter the updated dosage or quantity');
    setEditSaving(true);
    try {
      const fd = new FormData();
      fd.append('request_type', 'MEDICATION_CHANGE');
      fd.append('action', 'MODIFY');
      fd.append('payload', JSON.stringify({
        drug_name: med.drug_name,
        ProcedureName: med.drug_name,
        ProcedureId: med.pbm_drug_id || '',
        EntryNo: med.pbm_drug_id || '',
        ProcedureQuantity: parseInt(editQty) || 1,
        DosageDescription: editDosage,
        Comment: editComment,
      }));
      fd.append('comment', editComment || `Updated dosage for ${med.drug_name}`);
      await api.post('/requests', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      alert(`${med.drug_name} update has been submitted.`);
      cancelEdit();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to update'); }
    finally { setEditSaving(false); }
  };

  return (
    <div>
      <div style={s.header}>
        <div>
          <h1 style={s.heading}>My Medications</h1>
          <p style={s.sub}>Your current medication list.</p>
        </div>
        <div style={s.headerActions}>
          <button style={s.addBtn} onClick={() => navigate('/new-request')}>+ Add Medication</button>
          <button style={s.refillAllBtn} onClick={requestAllRefills} disabled={loading}>
            {loading ? 'Requesting...' : 'Request All Refills'}
          </button>
        </div>
      </div>

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
              <Detail label="Days Supply" value={`${m.days_supply} days`} />
              <Detail label="Refills Used" value={`${m.refill_count} / ${m.max_refills}`} />
            </div>

            <div style={s.refillDate}>
              <span style={s.refillLabel}>Next Refill Date:</span>
              <span style={s.refillValue}>
                {m.next_refill_due
                  ? new Date(m.next_refill_due).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
                  : 'Not scheduled'}
              </span>
              {m.days_until_runout != null && m.days_until_runout <= 7 && (
                <span style={s.urgentTag}>{m.days_until_runout <= 0 ? 'OVERDUE' : `${m.days_until_runout}d left`}</span>
              )}
            </div>

            {/* Edit form (inline) */}
            {editingMed === m.id ? (
              <div style={s.editForm}>
                <div style={s.editTitle}>Edit {m.drug_name}</div>
                <label style={s.editLabel}>New Dosage / Directions</label>
                <input style={s.editInput} value={editDosage} onChange={e => setEditDosage(e.target.value)}
                  placeholder="e.g. Two tabs twice daily" />
                <label style={s.editLabel}>Quantity</label>
                <input style={s.editInput} type="number" value={editQty} onChange={e => setEditQty(e.target.value)}
                  placeholder="e.g. 3" min="1" />
                <label style={s.editLabel}>Reason for change</label>
                <input style={s.editInput} value={editComment} onChange={e => setEditComment(e.target.value)}
                  placeholder="e.g. Doctor increased dosage" />
                <div style={s.editBtns}>
                  <button style={s.editSaveBtn} onClick={() => saveEdit(m)} disabled={editSaving}>
                    {editSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button style={s.editCancelBtn} onClick={cancelEdit}>Cancel</button>
                </div>
              </div>
            ) : (
              <div style={s.actions}>
                <button style={s.refillBtn} onClick={() => requestRefill(m)}>Request Refill</button>
                <button style={s.editBtn} onClick={() => startEdit(m)}>Edit</button>
                <button style={s.deleteBtn} onClick={() => deleteMedication(m)}>Delete</button>
              </div>
            )}
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
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 12 },
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, fontSize: 14 },
  headerActions: { display: 'flex', gap: 10 },
  addBtn: { padding: '10px 20px', borderRadius: 8, border: '2px solid #C8102E', backgroundColor: '#fff', color: '#C8102E', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  refillAllBtn: { padding: '10px 20px', borderRadius: 8, border: 'none', backgroundColor: '#1A1A2E', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 22, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  cardHead: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  drug: { fontSize: 17, fontWeight: 700, color: '#1A1A2E' },
  generic: { fontSize: 13, color: '#666' },
  badge: { padding: '3px 10px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600, flexShrink: 0 },
  detailGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 },
  refillDate: { marginTop: 14, padding: '10px 14px', backgroundColor: '#F0F4FF', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 8 },
  refillLabel: { fontSize: 12, color: '#666', fontWeight: 600 },
  refillValue: { fontSize: 14, fontWeight: 700, color: '#1A1A2E' },
  urgentTag: { padding: '2px 8px', borderRadius: 4, backgroundColor: '#FEE2E2', color: '#DC2626', fontSize: 11, fontWeight: 700 },
  actions: { display: 'flex', gap: 8, marginTop: 14 },
  refillBtn: { flex: 1, padding: '10px', borderRadius: 8, border: 'none', backgroundColor: '#1A1A2E', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  editBtn: { padding: '10px 16px', borderRadius: 8, border: '1px solid #2563EB', backgroundColor: '#fff', color: '#2563EB', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  deleteBtn: { padding: '10px 16px', borderRadius: 8, border: '1px solid #DC2626', backgroundColor: '#fff', color: '#DC2626', fontSize: 13, fontWeight: 600, cursor: 'pointer' },

  // Edit form
  editForm: { marginTop: 14, padding: 16, backgroundColor: '#F8F8FA', borderRadius: 10, border: '1px solid #ddd' },
  editTitle: { fontSize: 14, fontWeight: 700, color: '#1A1A2E', marginBottom: 10 },
  editLabel: { fontSize: 12, fontWeight: 600, color: '#444', marginTop: 8, display: 'block' },
  editInput: { width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #ddd', fontSize: 13, marginTop: 4, boxSizing: 'border-box' },
  editBtns: { display: 'flex', gap: 8, marginTop: 12 },
  editSaveBtn: { flex: 1, padding: '10px', borderRadius: 8, border: 'none', backgroundColor: '#2563EB', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
  editCancelBtn: { padding: '10px 16px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', color: '#666', fontSize: 13, fontWeight: 600, cursor: 'pointer' },
};
