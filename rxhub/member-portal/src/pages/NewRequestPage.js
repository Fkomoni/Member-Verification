import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function NewRequestPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  // Profile fields
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newAddress, setNewAddress] = useState('');
  const [newCity, setNewCity] = useState('');
  const [newState, setNewState] = useState('');
  const [altPhone, setAltPhone] = useState('');
  const [profileComment, setProfileComment] = useState('');

  // Medication fields
  const [medAction, setMedAction] = useState('ADD');
  const [drugName, setDrugName] = useState('');
  const [procedureId, setProcedureId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [diagnosisName, setDiagnosisName] = useState('');
  const [diagnosisId, setDiagnosisId] = useState('');
  const [medComment, setMedComment] = useState('');
  const [file, setFile] = useState(null);

  // Medication search/autocomplete
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searching, setSearching] = useState(false);
  const searchTimeout = useRef(null);

  // Debounced medication search
  useEffect(() => {
    if (searchTerm.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      setSearching(true);
      try {
        const { data } = await api.get('/member/search-medications', { params: { q: searchTerm } });
        setSearchResults(data);
        setShowDropdown(data.length > 0);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchTerm]);

  const selectMedication = (med) => {
    setDrugName(med.procedure_name);
    setProcedureId(med.procedure_id);
    setSearchTerm(med.procedure_name);
    setShowDropdown(false);
  };

  const submitProfile = async () => {
    if (!newPhone && !newEmail && !newAddress) return alert('Enter at least one field to update');
    setLoading(true);
    try {
      await api.post('/member/profile/update-request', {
        new_phone: newPhone || undefined,
        new_email: newEmail || undefined,
        new_address: newAddress || undefined,
        comment: profileComment || undefined,
      });
      alert('Profile update request submitted!');
      navigate('/requests');
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const submitMedication = async () => {
    if (!drugName) return alert('Please search and select a medication');
    if (medAction === 'ADD' && !medComment) return alert('Comment required for new medication requests');
    setLoading(true);
    try {
      const payload = {
        drug_name: drugName,
        ProcedureName: drugName,
        ProcedureId: procedureId,
        ProcedureQuantity: parseInt(quantity) || 1,
        DiagnosisName: diagnosisName,
        DiagnosisId: diagnosisId,
      };

      if (medAction === 'MODIFY') {
        payload.new_dosage = quantity;
      }

      const fd = new FormData();
      fd.append('request_type', 'MEDICATION_CHANGE');
      fd.append('action', medAction);
      fd.append('payload', JSON.stringify(payload));
      if (medComment) fd.append('comment', medComment);
      if (file) fd.append('attachment', file);

      await api.post('/requests', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      alert('Medication request submitted!');
      navigate('/requests');
    } catch (err) { alert(err.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <h1 style={s.heading}>New Request</h1>
      <p style={s.sub}>Submit a profile update or medication change request</p>

      <div style={s.tabs}>
        <button style={{ ...s.tab, ...(tab === 'profile' ? s.tabActive : {}) }} onClick={() => setTab('profile')}>Profile Update</button>
        <button style={{ ...s.tab, ...(tab === 'medication' ? s.tabActive : {}) }} onClick={() => setTab('medication')}>Medication Change</button>
      </div>

      {/* ── PROFILE UPDATE ── */}
      {tab === 'profile' && (
        <div style={s.card}>
          <h2 style={s.cardTitle}>Update Your Profile</h2>
          <p style={s.cardSub}>Only fill fields you want to change. Changes go through approval and sync to Prognosis.</p>

          <label style={s.label}>New Phone Number</label>
          <input style={s.input} value={newPhone} onChange={e => setNewPhone(e.target.value)} placeholder="e.g. 08098765432" />

          <label style={s.label}>Alternative Phone Number</label>
          <input style={s.input} value={altPhone} onChange={e => setAltPhone(e.target.value)} placeholder="e.g. 09029393088" />

          <label style={s.label}>New Email Address</label>
          <input style={s.input} value={newEmail} onChange={e => setNewEmail(e.target.value)} placeholder="e.g. new@email.com" />

          <label style={s.label}>New Address</label>
          <input style={s.input} value={newAddress} onChange={e => setNewAddress(e.target.value)} placeholder="e.g. 12 Oshoala Street" />

          <div style={s.row2}>
            <div style={s.halfField}>
              <label style={s.label}>City</label>
              <input style={s.input} value={newCity} onChange={e => setNewCity(e.target.value)} placeholder="e.g. Ikeja" />
            </div>
            <div style={s.halfField}>
              <label style={s.label}>State</label>
              <input style={s.input} value={newState} onChange={e => setNewState(e.target.value)} placeholder="e.g. Lagos" />
            </div>
          </div>

          <label style={s.label}>Reason (Optional)</label>
          <input style={s.input} value={profileComment} onChange={e => setProfileComment(e.target.value)} placeholder="e.g. Relocated to new address" />

          <button style={s.btn} onClick={submitProfile} disabled={loading}>{loading ? 'Submitting...' : 'Submit Profile Update'}</button>
        </div>
      )}

      {/* ── MEDICATION CHANGE ── */}
      {tab === 'medication' && (
        <div style={s.card}>
          <h2 style={s.cardTitle}>Medication Change</h2>

          <div style={s.actionRow}>
            {['ADD', 'REMOVE', 'MODIFY'].map(a => (
              <button key={a} style={{ ...s.actionBtn, ...(medAction === a ? s.actionBtnActive : {}) }}
                onClick={() => { setMedAction(a); setDrugName(''); setProcedureId(''); setSearchTerm(''); }}>
                {a === 'ADD' ? 'Add New' : a === 'REMOVE' ? 'Remove' : 'Modify'}
              </button>
            ))}
          </div>

          {/* Medication Search with Autocomplete */}
          <label style={s.label}>Search Medication</label>
          <div style={s.searchWrap}>
            <input
              style={s.searchInput}
              value={searchTerm}
              onChange={e => { setSearchTerm(e.target.value); setDrugName(''); setProcedureId(''); }}
              placeholder="Start typing medication name..."
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
            />
            {searching && <span style={s.searchSpinner}>Searching...</span>}

            {showDropdown && (
              <div style={s.dropdown}>
                {searchResults.map((med, i) => (
                  <div key={i} style={s.dropdownItem} onClick={() => selectMedication(med)}>
                    <div style={s.dropdownName}>{med.procedure_name}</div>
                    <div style={s.dropdownId}>ID: {med.procedure_id}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {drugName && (
            <div style={s.selectedMed}>
              Selected: <strong>{drugName}</strong> {procedureId && <span style={s.selectedId}>(ID: {procedureId})</span>}
            </div>
          )}

          {(medAction === 'ADD' || medAction === 'MODIFY') && (
            <>
              <label style={s.label}>Quantity</label>
              <input style={s.input} type="number" value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="e.g. 3" min="1" />

              <label style={s.label}>Diagnosis</label>
              <input style={s.input} value={diagnosisName} onChange={e => setDiagnosisName(e.target.value)} placeholder="e.g. Essential (primary) hypertension" />

              <label style={s.label}>Diagnosis Code (if known)</label>
              <input style={s.input} value={diagnosisId} onChange={e => setDiagnosisId(e.target.value)} placeholder="e.g. I10" />
            </>
          )}

          <label style={s.label}>Comment / Reason</label>
          <textarea style={{ ...s.input, minHeight: 70 }} value={medComment} onChange={e => setMedComment(e.target.value)}
            placeholder={medAction === 'ADD' ? 'Why do you need this medication? (Required)' : 'Reason for this change...'} />

          {medAction === 'ADD' && (
            <>
              <label style={s.label}>Prescription Upload (if available)</label>
              <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e => setFile(e.target.files[0])} style={{ fontSize: 13, marginBottom: 8 }} />
            </>
          )}

          <button style={s.btn} onClick={submitMedication} disabled={loading}>{loading ? 'Submitting...' : 'Submit Medication Request'}</button>
        </div>
      )}
    </div>
  );
}

const s = {
  heading: { fontSize: 26, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  sub: { color: '#666', marginTop: 4, marginBottom: 20, fontSize: 14 },
  tabs: { display: 'flex', gap: 8, marginBottom: 20 },
  tab: { padding: '10px 20px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 500 },
  tabActive: { backgroundColor: '#262626', color: '#fff', borderColor: '#262626' },
  card: { backgroundColor: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 3px rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 580 },
  cardTitle: { fontSize: 18, fontWeight: 700, color: '#1A1A2E', margin: 0 },
  cardSub: { fontSize: 13, color: '#666', margin: '0 0 8px' },
  label: { fontSize: 12, fontWeight: 600, color: '#444', marginTop: 4 },
  input: { padding: '10px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14 },
  row2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  halfField: { display: 'flex', flexDirection: 'column', gap: 4 },
  btn: { padding: '12px', borderRadius: 8, border: 'none', backgroundColor: '#C8102E', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer', marginTop: 8 },
  actionRow: { display: 'flex', gap: 8, marginBottom: 8 },
  actionBtn: { padding: '8px 16px', borderRadius: 8, border: '1px solid #ddd', backgroundColor: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  actionBtnActive: { backgroundColor: '#262626', color: '#fff', borderColor: '#262626' },

  // Search autocomplete
  searchWrap: { position: 'relative' },
  searchInput: { width: '100%', padding: '12px 14px', borderRadius: 8, border: '2px solid #C8102E', fontSize: 15, outline: 'none', boxSizing: 'border-box' },
  searchSpinner: { position: 'absolute', right: 14, top: 14, fontSize: 12, color: '#999' },
  dropdown: {
    position: 'absolute', top: '100%', left: 0, right: 0, backgroundColor: '#fff',
    border: '1px solid #ddd', borderRadius: '0 0 8px 8px', maxHeight: 250, overflowY: 'auto',
    zIndex: 100, boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
  },
  dropdownItem: { padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid #f0f0f0', transition: 'background 0.1s' },
  dropdownName: { fontSize: 14, fontWeight: 600, color: '#1A1A2E' },
  dropdownId: { fontSize: 11, color: '#999', marginTop: 2 },
  selectedMed: { padding: '10px 14px', backgroundColor: '#F0FDF4', borderRadius: 8, fontSize: 14, color: '#16A34A', marginTop: 4 },
  selectedId: { fontSize: 12, color: '#666' },
};
