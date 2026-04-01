import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import api from '../services/api';

export default function DashboardScreen({ navigation }) {
  const [dashboard, setDashboard] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboard = async () => {
    try {
      const { data } = await api.get('/member/dashboard');
      setDashboard(data);
    } catch {}
  };

  useFocusEffect(useCallback(() => { fetchDashboard(); }, []));

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchDashboard();
    setRefreshing(false);
  };

  if (!dashboard) return <View style={styles.container}><Text style={styles.loading}>Loading...</Text></View>;

  const { profile, medications_count, pending_requests, unread_notifications, alerts } = dashboard;

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#C8102E" />}>
      <View style={styles.welcomeCard}>
        <Text style={styles.welcomeText}>Welcome back,</Text>
        <Text style={styles.nameText}>{profile.first_name} {profile.last_name}</Text>
        <Text style={styles.memberIdText}>ID: {profile.member_id}</Text>
        {profile.diagnosis && <Text style={styles.diagnosisText}>Diagnosis: {profile.diagnosis}</Text>}
      </View>

      <View style={styles.statsRow}>
        <StatBox label="Medications" value={medications_count} color="#1A1A2E" />
        <StatBox label="Pending" value={pending_requests} color="#E87722" />
        <StatBox label="Notifications" value={unread_notifications} color="#C8102E" />
      </View>

      {alerts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Alerts</Text>
          {alerts.map((alert, i) => (
            <View key={i} style={styles.alertCard}>
              <Text style={styles.alertDrug}>{alert.medication}</Text>
              <Text style={styles.alertMsg}>{alert.message}</Text>
              {alert.days_remaining != null && (
                <Text style={styles.alertDays}>{alert.days_remaining} days remaining</Text>
              )}
            </View>
          ))}
        </View>
      )}

      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <ActionBtn label="Request Refill" onPress={() => navigation.navigate('Refill')} color="#1A1A2E" />
          <ActionBtn label="New Request" onPress={() => navigation.navigate('NewRequest')} color="#C8102E" />
          <ActionBtn label="Make Payment" onPress={() => navigation.navigate('Payment')} color="#E87722" />
        </View>
      </View>

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

function StatBox({ label, value, color }) {
  return (
    <View style={[styles.statBox, { borderTopColor: color }]}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function ActionBtn({ label, onPress, color }) {
  return (
    <TouchableOpacity style={[styles.actionBtn, { backgroundColor: color }]} onPress={onPress}>
      <Text style={styles.actionBtnText}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  loading: { textAlign: 'center', marginTop: 100, color: '#999' },
  welcomeCard: {
    backgroundColor: '#1A1A2E', padding: 24, paddingTop: 16, paddingBottom: 28,
    borderBottomLeftRadius: 24, borderBottomRightRadius: 24,
  },
  welcomeText: { color: 'rgba(255,255,255,0.6)', fontSize: 14 },
  nameText: { color: '#fff', fontSize: 24, fontWeight: '700', marginTop: 4 },
  memberIdText: { color: 'rgba(255,255,255,0.5)', fontSize: 13, marginTop: 4 },
  diagnosisText: { color: '#E87722', fontSize: 13, marginTop: 4 },
  statsRow: { flexDirection: 'row', paddingHorizontal: 16, marginTop: -16, gap: 10 },
  statBox: {
    flex: 1, backgroundColor: '#fff', borderRadius: 12, padding: 16,
    borderTopWidth: 3, shadowColor: '#000', shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2,
  },
  statValue: { fontSize: 28, fontWeight: '700', color: '#1A1A2E' },
  statLabel: { fontSize: 12, color: '#666', marginTop: 2 },
  section: { padding: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 12 },
  alertCard: {
    backgroundColor: '#FFF7ED', borderRadius: 12, padding: 16, marginBottom: 8,
    borderLeftWidth: 4, borderLeftColor: '#E87722',
  },
  alertDrug: { fontSize: 15, fontWeight: '700', color: '#1A1A2E' },
  alertMsg: { fontSize: 13, color: '#666', marginTop: 4 },
  alertDays: { fontSize: 12, color: '#E87722', fontWeight: '600', marginTop: 4 },
  quickActions: { padding: 16 },
  actionsRow: { flexDirection: 'row', gap: 10 },
  actionBtn: { flex: 1, borderRadius: 12, padding: 16, alignItems: 'center' },
  actionBtnText: { color: '#fff', fontSize: 13, fontWeight: '700' },
});
