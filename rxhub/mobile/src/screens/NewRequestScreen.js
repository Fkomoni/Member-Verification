import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import api from '../services/api';

const REQUEST_TYPES = ['MEDICATION_CHANGE', 'PROFILE_UPDATE'];
const ACTIONS = {
  MEDICATION_CHANGE: ['ADD', 'REMOVE', 'MODIFY'],
  PROFILE_UPDATE: ['MODIFY'],
};

export default function NewRequestScreen({ navigation }) {
  const [requestType, setRequestType] = useState('MEDICATION_CHANGE');
  const [action, setAction] = useState('ADD');
  const [comment, setComment] = useState('');
  const [drugName, setDrugName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);

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

  const handleSubmit = async () => {
    if (requestType === 'MEDICATION_CHANGE' && action === 'ADD') {
      if (!drugName || !dosage || !frequency || !comment) {
        Alert.alert('Error', 'Please fill all fields and add a comment');
        return;
      }
      if (!file) {
        Alert.alert('Error', 'Prescription upload required for new medications');
        return;
      }
    }

    setLoading(true);
    try {
      const payload = requestType === 'MEDICATION_CHANGE'
        ? { drug_name: drugName, dosage, frequency }
        : { comment };

      const formData = new FormData();
      formData.append('request_type', requestType);
      formData.append('action', action);
      formData.append('payload', JSON.stringify(payload));
      formData.append('comment', comment);

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

      Alert.alert('Success', 'Request submitted successfully', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Failed to submit request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <Text style={styles.sectionTitle}>Request Type</Text>
      <View style={styles.btnRow}>
        {REQUEST_TYPES.map(t => (
          <TouchableOpacity
            key={t}
            style={[styles.typeBtn, requestType === t && styles.typeBtnActive]}
            onPress={() => { setRequestType(t); setAction(ACTIONS[t][0]); }}
          >
            <Text style={[styles.typeBtnText, requestType === t && styles.typeBtnTextActive]}>
              {t.replace(/_/g, ' ')}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Action</Text>
      <View style={styles.btnRow}>
        {ACTIONS[requestType].map(a => (
          <TouchableOpacity
            key={a}
            style={[styles.typeBtn, action === a && styles.typeBtnActive]}
            onPress={() => setAction(a)}
          >
            <Text style={[styles.typeBtnText, action === a && styles.typeBtnTextActive]}>{a}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {requestType === 'MEDICATION_CHANGE' && (
        <>
          <Text style={styles.sectionTitle}>Medication Details</Text>
          <TextInput style={styles.input} placeholder="Drug Name" value={drugName} onChangeText={setDrugName} />
          <TextInput style={styles.input} placeholder="Dosage (e.g. 500mg)" value={dosage} onChangeText={setDosage} />
          <TextInput style={styles.input} placeholder="Frequency (e.g. twice daily)" value={frequency} onChangeText={setFrequency} />
        </>
      )}

      <Text style={styles.sectionTitle}>Comment</Text>
      <TextInput
        style={[styles.input, { minHeight: 80, textAlignVertical: 'top' }]}
        placeholder="Add a comment or reason..."
        value={comment} onChangeText={setComment} multiline
      />

      {action === 'ADD' && requestType === 'MEDICATION_CHANGE' && (
        <>
          <Text style={styles.sectionTitle}>Prescription Upload (Required)</Text>
          <TouchableOpacity style={styles.uploadBtn} onPress={pickFile}>
            <Text style={styles.uploadBtnText}>{file ? file.name : 'Choose File (PDF, JPG, PNG)'}</Text>
          </TouchableOpacity>
        </>
      )}

      <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit} disabled={loading}>
        <Text style={styles.submitBtnText}>{loading ? 'Submitting...' : 'Submit Request'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: '#1A1A2E', marginTop: 20, marginBottom: 8 },
  btnRow: { flexDirection: 'row', gap: 8 },
  typeBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E5E5E5' },
  typeBtnActive: { backgroundColor: '#1A1A2E', borderColor: '#1A1A2E' },
  typeBtnText: { fontSize: 13, fontWeight: '600', color: '#666' },
  typeBtnTextActive: { color: '#fff' },
  input: { backgroundColor: '#fff', borderRadius: 10, padding: 14, fontSize: 15, borderWidth: 1, borderColor: '#E5E5E5', marginBottom: 10 },
  uploadBtn: { backgroundColor: '#fff', borderRadius: 10, padding: 16, borderWidth: 1, borderColor: '#E87722', borderStyle: 'dashed', alignItems: 'center' },
  uploadBtnText: { color: '#E87722', fontWeight: '600', fontSize: 14 },
  submitBtn: { backgroundColor: '#C8102E', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  submitBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
