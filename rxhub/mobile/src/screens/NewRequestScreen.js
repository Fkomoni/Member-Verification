import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import api from '../services/api';

const REQUEST_TYPES = [
  { key: 'PROFILE_UPDATE', label: 'Profile Update' },
  { key: 'MEDICATION_CHANGE', label: 'Medication Change' },
];

const ACTIONS = {
  MEDICATION_CHANGE: [
    { key: 'ADD', label: 'Add New' },
    { key: 'REMOVE', label: 'Remove' },
    { key: 'MODIFY', label: 'Modify' },
  ],
  PROFILE_UPDATE: [
    { key: 'MODIFY', label: 'Update Info' },
  ],
};

export default function NewRequestScreen({ navigation }) {
  const [requestType, setRequestType] = useState('PROFILE_UPDATE');
  const [action, setAction] = useState('MODIFY');
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(false);

  // Profile update fields
  const [newPhone, setNewPhone] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newAddress, setNewAddress] = useState('');

  // Medication fields
  const [drugName, setDrugName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [medicationId, setMedicationId] = useState('');
  const [file, setFile] = useState(null);

  const pickFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/jpeg', 'image/png'],
      });
      if (!result.canceled && result.assets?.[0]) {
        setFile(result.assets[0]);
      }
    } catch {}
  };

  const buildPayload = () => {
    if (requestType === 'PROFILE_UPDATE') {
      const changes = {};
      if (newPhone.trim()) changes.phone = newPhone.trim();
      if (newEmail.trim()) changes.email = newEmail.trim();
      if (newAddress.trim()) changes.address = newAddress.trim();

      if (Object.keys(changes).length === 0) {
        Alert.alert('Error', 'Please enter at least one field to update');
        return null;
      }
      return changes;
    }

    if (requestType === 'MEDICATION_CHANGE') {
      if (action === 'ADD') {
        if (!drugName || !dosage || !frequency) {
          Alert.alert('Error', 'Please fill drug name, dosage, and frequency');
          return null;
        }
        if (!comment) {
          Alert.alert('Error', 'Comment required for new medication requests');
          return null;
        }
        if (!file) {
          Alert.alert('Error', 'Prescription upload required for new medications');
          return null;
        }
        return { drug_name: drugName, dosage, frequency };
      }
      if (action === 'REMOVE') {
        if (!drugName && !medicationId) {
          Alert.alert('Error', 'Please enter the medication name to remove');
          return null;
        }
        return { drug_name: drugName, medication_id: medicationId };
      }
      if (action === 'MODIFY') {
        if (!drugName) {
          Alert.alert('Error', 'Please enter the medication name to modify');
          return null;
        }
        return { drug_name: drugName, new_dosage: dosage, new_frequency: frequency };
      }
    }

    return {};
  };

  const handleSubmit = async () => {
    const payload = buildPayload();
    if (!payload) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('request_type', requestType);
      formData.append('action', action);
      formData.append('payload', JSON.stringify(payload));
      if (comment) formData.append('comment', comment);

      if (file) {
        formData.append('attachment', {
          uri: file.uri,
          name: file.name,
          type: file.mimeType || 'application/octet-stream',
        });
      }

      await api.post('/requests', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      Alert.alert('Success', 'Request submitted successfully! You will be notified once it is reviewed.', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Failed to submit request');
    } finally {
      setLoading(false);
    }
  };

  const switchType = (key) => {
    setRequestType(key);
    setAction(ACTIONS[key][0].key);
    // Reset fields
    setNewPhone(''); setNewEmail(''); setNewAddress('');
    setDrugName(''); setDosage(''); setFrequency(''); setMedicationId('');
    setFile(null); setComment('');
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>

      {/* Request Type Selector */}
      <Text style={styles.sectionTitle}>What would you like to do?</Text>
      <View style={styles.btnRow}>
        {REQUEST_TYPES.map(t => (
          <TouchableOpacity
            key={t.key}
            style={[styles.typeBtn, requestType === t.key && styles.typeBtnActive]}
            onPress={() => switchType(t.key)}
          >
            <Text style={[styles.typeBtnText, requestType === t.key && styles.typeBtnTextActive]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* ── PROFILE UPDATE ── */}
      {requestType === 'PROFILE_UPDATE' && (
        <View style={styles.formCard}>
          <Text style={styles.cardTitle}>Update Your Profile</Text>
          <Text style={styles.cardSubtitle}>Enter the new value(s) you want updated. Only fill the fields you want to change.</Text>

          <Text style={styles.label}>New Phone Number</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. 08098765432"
            value={newPhone}
            onChangeText={setNewPhone}
            keyboardType="phone-pad"
          />

          <Text style={styles.label}>New Email Address</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. newemail@example.com"
            value={newEmail}
            onChangeText={setNewEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Text style={styles.label}>New Address</Text>
          <TextInput
            style={[styles.input, { minHeight: 60, textAlignVertical: 'top' }]}
            placeholder="Enter your new address..."
            value={newAddress}
            onChangeText={setNewAddress}
            multiline
          />

          <Text style={styles.label}>Reason for Change (Optional)</Text>
          <TextInput
            style={[styles.input, { minHeight: 60, textAlignVertical: 'top' }]}
            placeholder="e.g. Changed phone carrier, moved to new address..."
            value={comment}
            onChangeText={setComment}
            multiline
          />
        </View>
      )}

      {/* ── MEDICATION CHANGE ── */}
      {requestType === 'MEDICATION_CHANGE' && (
        <>
          <Text style={styles.sectionTitle}>Action</Text>
          <View style={styles.btnRow}>
            {ACTIONS.MEDICATION_CHANGE.map(a => (
              <TouchableOpacity
                key={a.key}
                style={[styles.typeBtn, action === a.key && styles.typeBtnActive]}
                onPress={() => setAction(a.key)}
              >
                <Text style={[styles.typeBtnText, action === a.key && styles.typeBtnTextActive]}>
                  {a.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.formCard}>
            <Text style={styles.cardTitle}>
              {action === 'ADD' ? 'Add New Medication' : action === 'REMOVE' ? 'Remove Medication' : 'Modify Medication'}
            </Text>

            <Text style={styles.label}>Medication Name</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. Amlodipine"
              value={drugName}
              onChangeText={setDrugName}
            />

            {(action === 'ADD' || action === 'MODIFY') && (
              <>
                <Text style={styles.label}>{action === 'MODIFY' ? 'New Dosage' : 'Dosage'}</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. 500mg"
                  value={dosage}
                  onChangeText={setDosage}
                />

                <Text style={styles.label}>{action === 'MODIFY' ? 'New Frequency' : 'Frequency'}</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Twice daily"
                  value={frequency}
                  onChangeText={setFrequency}
                />
              </>
            )}

            <Text style={styles.label}>Comment / Reason</Text>
            <TextInput
              style={[styles.input, { minHeight: 80, textAlignVertical: 'top' }]}
              placeholder={action === 'ADD'
                ? 'Why do you need this medication? (Required)'
                : action === 'REMOVE'
                ? 'Reason for stopping this medication...'
                : 'Reason for dosage/frequency change...'}
              value={comment}
              onChangeText={setComment}
              multiline
            />

            {action === 'ADD' && (
              <>
                <Text style={styles.label}>Prescription Upload (Required)</Text>
                <TouchableOpacity style={styles.uploadBtn} onPress={pickFile}>
                  <Text style={styles.uploadIcon}>{file ? '\u2705' : '\u{1F4CE}'}</Text>
                  <Text style={styles.uploadBtnText}>
                    {file ? file.name : 'Choose File (PDF, JPG, PNG)'}
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </>
      )}

      {/* Submit */}
      <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit} disabled={loading}>
        <Text style={styles.submitBtnText}>{loading ? 'Submitting...' : 'Submit Request'}</Text>
      </TouchableOpacity>

      <Text style={styles.disclaimerText}>
        All changes go through our review process. You'll be notified once your request is approved or if we need more information.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: '#1A1A2E', marginTop: 20, marginBottom: 10 },
  btnRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  typeBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E5E5E5' },
  typeBtnActive: { backgroundColor: '#1A1A2E', borderColor: '#1A1A2E' },
  typeBtnText: { fontSize: 13, fontWeight: '600', color: '#666' },
  typeBtnTextActive: { color: '#fff' },
  formCard: {
    backgroundColor: '#fff', borderRadius: 14, padding: 20, marginTop: 16,
    shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2,
  },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  cardSubtitle: { fontSize: 13, color: '#666', marginBottom: 16, lineHeight: 18 },
  label: { fontSize: 13, fontWeight: '600', color: '#444', marginTop: 12, marginBottom: 6 },
  input: {
    backgroundColor: '#F8F8FA', borderRadius: 10, padding: 14, fontSize: 15,
    borderWidth: 1, borderColor: '#E5E5E5',
  },
  uploadBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    backgroundColor: '#FFF7ED', borderRadius: 10, padding: 16,
    borderWidth: 1, borderColor: '#E87722', borderStyle: 'dashed',
  },
  uploadIcon: { fontSize: 18 },
  uploadBtnText: { color: '#E87722', fontWeight: '600', fontSize: 14 },
  submitBtn: { backgroundColor: '#C8102E', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  disclaimerText: { fontSize: 12, color: '#999', textAlign: 'center', marginTop: 16, lineHeight: 18, paddingHorizontal: 12 },
});
