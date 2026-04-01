import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import api from '../services/api';

const STATUS_COLORS = {
  PENDING: '#E87722', REVIEWED: '#2563EB', APPROVED: '#16A34A',
  REJECTED: '#DC2626', MODIFIED: '#7C3AED',
};

export default function RequestsScreen() {
  const [requests, setRequests] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = async () => {
    try {
      const { data } = await api.get('/requests/my', { params: { page_size: 50 } });
      setRequests(data.requests);
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
        <View>
          <Text style={styles.type}>{item.request_type.replace(/_/g, ' ')}</Text>
          <Text style={styles.action}>{item.action}</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: STATUS_COLORS[item.status] || '#999' }]}>
          <Text style={styles.badgeText}>{item.status}</Text>
        </View>
      </View>

      {item.comment && <Text style={styles.comment}>{item.comment}</Text>}

      {item.admin_comment && (
        <View style={styles.adminReply}>
          <Text style={styles.adminLabel}>Admin Response:</Text>
          <Text style={styles.adminText}>{item.admin_comment}</Text>
        </View>
      )}

      <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString()}</Text>
    </View>
  );

  return (
    <FlatList
      style={styles.container}
      data={requests}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#C8102E" />}
      ListEmptyComponent={<Text style={styles.empty}>No requests yet</Text>}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 20, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  type: { fontSize: 11, fontWeight: '700', color: '#999', textTransform: 'uppercase' },
  action: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginTop: 2 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  badgeText: { color: '#fff', fontSize: 11, fontWeight: '700' },
  comment: { fontSize: 14, color: '#444', marginTop: 12, lineHeight: 20 },
  adminReply: { marginTop: 12, backgroundColor: '#F0FDF4', borderRadius: 8, padding: 12 },
  adminLabel: { fontSize: 11, fontWeight: '700', color: '#16A34A' },
  adminText: { fontSize: 13, color: '#333', marginTop: 4 },
  date: { fontSize: 12, color: '#999', marginTop: 12 },
  empty: { textAlign: 'center', color: '#999', marginTop: 60 },
});
