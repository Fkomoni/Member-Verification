import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import api from '../services/api';

export default function MedicationsScreen({ navigation }) {
  const [medications, setMedications] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = async () => {
    try {
      const { data } = await api.get('/member/medications');
      setMedications(data);
    } catch {}
  };

  useFocusEffect(useCallback(() => { fetch(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await fetch();
    setRefreshing(false);
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.drugName}>{item.drug_name}</Text>
        <View style={[styles.statusBadge, { backgroundColor: item.status === 'ACTIVE' ? '#16A34A' : '#999' }]}>
          <Text style={styles.statusText}>{item.status}</Text>
        </View>
      </View>

      {item.generic_name && <Text style={styles.generic}>{item.generic_name}</Text>}

      <View style={styles.detailRow}>
        <Detail label="Dosage" value={item.dosage} />
        <Detail label="Frequency" value={item.frequency} />
      </View>
      <View style={styles.detailRow}>
        <Detail label="Refills Used" value={`${item.refill_count}/${item.max_refills}`} />
        <Detail label="Days Supply" value={`${item.days_supply} days`} />
      </View>

      {item.days_until_runout != null && (
        <View style={[styles.runoutBar, item.days_until_runout <= 7 ? styles.runoutUrgent : {}]}>
          <Text style={styles.runoutText}>
            {item.days_until_runout <= 0
              ? 'Supply depleted — request refill now'
              : `${item.days_until_runout} days of supply remaining`}
          </Text>
        </View>
      )}

      {item.is_covered && (
        <Text style={styles.coverage}>Covered: {parseFloat(item.coverage_pct)}% | Copay: NGN {parseFloat(item.copay_amount).toLocaleString()}</Text>
      )}

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.refillBtn}
          onPress={() => navigation.navigate('Refill', { medication: item })}
        >
          <Text style={styles.refillBtnText}>Request Refill</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <FlatList
      style={styles.container}
      data={medications}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#C8102E" />}
      ListEmptyComponent={<Text style={styles.empty}>No medications found</Text>}
    />
  );
}

function Detail({ label, value }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 20, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  drugName: { fontSize: 17, fontWeight: '700', color: '#1A1A2E', flex: 1 },
  statusBadge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  statusText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  generic: { fontSize: 13, color: '#666', marginTop: 2 },
  detailRow: { flexDirection: 'row', marginTop: 12 },
  detailLabel: { fontSize: 11, color: '#999', fontWeight: '600' },
  detailValue: { fontSize: 14, color: '#333', marginTop: 2 },
  runoutBar: { backgroundColor: '#FFF7ED', borderRadius: 8, padding: 10, marginTop: 12, borderLeftWidth: 3, borderLeftColor: '#E87722' },
  runoutUrgent: { backgroundColor: '#FEE2E2', borderLeftColor: '#C8102E' },
  runoutText: { fontSize: 13, color: '#333', fontWeight: '500' },
  coverage: { fontSize: 12, color: '#16A34A', marginTop: 8 },
  actions: { marginTop: 12 },
  refillBtn: { backgroundColor: '#1A1A2E', borderRadius: 10, padding: 12, alignItems: 'center' },
  refillBtnText: { color: '#fff', fontSize: 14, fontWeight: '700' },
  empty: { textAlign: 'center', color: '#999', marginTop: 60 },
});
