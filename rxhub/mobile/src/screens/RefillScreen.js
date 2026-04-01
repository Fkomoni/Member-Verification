import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, TextInput } from 'react-native';
import api from '../services/api';

export default function RefillScreen({ route, navigation }) {
  const [intelligence, setIntelligence] = useState([]);
  const [comment, setComment] = useState('');
  const [loading, setLoading] = useState(true);
  const preselected = route.params?.medication;

  useEffect(() => {
    api.get('/refill/intelligence')
      .then(({ data }) => setIntelligence(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleRefill = async (medicationId) => {
    try {
      await api.post('/refill/request', { medication_id: medicationId, comment });
      Alert.alert('Success', 'Refill request submitted', [
        { text: 'OK', onPress: () => navigation.goBack() },
      ]);
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Failed to submit refill request');
    }
  };

  const handleSuspend = async (medicationId) => {
    Alert.alert('Suspend Refill', 'Are you sure you want to suspend refills?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Suspend',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.post('/refill/suspend', { medication_id: medicationId, reason: 'Suspended by member' });
            Alert.alert('Success', 'Refill suspension request submitted');
          } catch (err) {
            Alert.alert('Error', err.response?.data?.detail || 'Failed');
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.drugName}>{item.drug_name}</Text>

      <View style={styles.infoRow}>
        <View style={styles.infoBox}>
          <Text style={styles.infoLabel}>Days Left</Text>
          <Text style={[styles.infoValue, item.days_remaining != null && item.days_remaining <= 7 ? { color: '#C8102E' } : {}]}>
            {item.days_remaining ?? 'N/A'}
          </Text>
        </View>
        <View style={styles.infoBox}>
          <Text style={styles.infoLabel}>Refills Left</Text>
          <Text style={styles.infoValue}>{item.refills_remaining}</Text>
        </View>
        <View style={styles.infoBox}>
          <Text style={styles.infoLabel}>Next Due</Text>
          <Text style={styles.infoValue}>{item.next_refill_due || 'N/A'}</Text>
        </View>
      </View>

      {item.alert && (
        <View style={styles.alertBar}>
          <Text style={styles.alertText}>{item.alert}</Text>
        </View>
      )}

      <TextInput
        style={styles.commentInput}
        placeholder="Add a note (optional)"
        value={comment}
        onChangeText={setComment}
      />

      <View style={styles.actions}>
        <TouchableOpacity style={styles.refillBtn} onPress={() => handleRefill(item.medication_id)}>
          <Text style={styles.refillBtnText}>Request Refill</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.suspendBtn} onPress={() => handleSuspend(item.medication_id)}>
          <Text style={styles.suspendBtnText}>Suspend</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <FlatList
      style={styles.container}
      data={intelligence}
      keyExtractor={(item) => item.medication_id}
      renderItem={renderItem}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      ListEmptyComponent={<Text style={styles.empty}>{loading ? 'Loading...' : 'No active medications'}</Text>}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 20, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  drugName: { fontSize: 17, fontWeight: '700', color: '#1A1A2E' },
  infoRow: { flexDirection: 'row', marginTop: 12, gap: 8 },
  infoBox: { flex: 1, backgroundColor: '#F8F8FA', borderRadius: 8, padding: 10, alignItems: 'center' },
  infoLabel: { fontSize: 11, color: '#999', fontWeight: '600' },
  infoValue: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginTop: 2 },
  alertBar: { backgroundColor: '#FEE2E2', borderRadius: 8, padding: 10, marginTop: 12 },
  alertText: { fontSize: 13, color: '#C8102E', fontWeight: '500' },
  commentInput: { backgroundColor: '#F8F8FA', borderRadius: 8, padding: 12, marginTop: 12, fontSize: 14 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
  refillBtn: { flex: 1, backgroundColor: '#1A1A2E', borderRadius: 10, padding: 14, alignItems: 'center' },
  refillBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  suspendBtn: { flex: 1, backgroundColor: '#fff', borderRadius: 10, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: '#DC2626' },
  suspendBtnText: { color: '#DC2626', fontSize: 14, fontWeight: '700' },
  empty: { textAlign: 'center', color: '#999', marginTop: 60 },
});
