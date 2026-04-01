import React, { useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function ProfileScreen() {
  const [profile, setProfile] = useState(null);
  const { logout } = useAuth();

  useFocusEffect(useCallback(() => {
    api.get('/member/profile')
      .then(({ data }) => setProfile(data))
      .catch(() => {});
  }, []));

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: logout },
    ]);
  };

  if (!profile) return <View style={styles.container}><Text style={styles.loading}>Loading...</Text></View>;

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{profile.first_name[0]}{profile.last_name[0]}</Text>
        </View>
        <Text style={styles.name}>{profile.first_name} {profile.last_name}</Text>
        <Text style={styles.memberId}>{profile.member_id}</Text>
      </View>

      <View style={styles.card}>
        <ProfileField label="Email" value={profile.email || 'Not set'} />
        <ProfileField label="Phone" value={profile.phone} />
        <ProfileField label="Date of Birth" value={profile.date_of_birth || 'Not set'} />
        <ProfileField label="Gender" value={profile.gender || 'Not set'} />
        <ProfileField label="Diagnosis" value={profile.diagnosis || 'Not set'} />
        <ProfileField label="Plan" value={`${profile.plan_name || ''} (${profile.plan_type || ''})`} />
        <ProfileField label="Employer" value={profile.employer || 'Not set'} />
        <ProfileField label="Status" value={profile.status} />
      </View>

      <Text style={styles.readonlyNote}>Profile data is synced from your PBM record. To request changes, submit a Profile Update request.</Text>

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function ProfileField({ label, value }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Text style={styles.fieldValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  loading: { textAlign: 'center', marginTop: 100, color: '#999' },
  header: { alignItems: 'center', marginBottom: 24 },
  avatar: {
    width: 72, height: 72, borderRadius: 36, backgroundColor: '#1A1A2E',
    justifyContent: 'center', alignItems: 'center', marginBottom: 12,
  },
  avatarText: { color: '#fff', fontSize: 24, fontWeight: '700' },
  name: { fontSize: 22, fontWeight: '700', color: '#1A1A2E' },
  memberId: { fontSize: 14, color: '#666', marginTop: 2 },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 20, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  field: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  fieldLabel: { fontSize: 12, color: '#999', fontWeight: '600' },
  fieldValue: { fontSize: 15, color: '#1A1A2E', marginTop: 4 },
  readonlyNote: { fontSize: 12, color: '#999', textAlign: 'center', marginTop: 16, paddingHorizontal: 20, lineHeight: 18 },
  logoutBtn: {
    marginTop: 32, backgroundColor: '#fff', borderRadius: 12, padding: 16,
    alignItems: 'center', borderWidth: 1, borderColor: '#DC2626',
  },
  logoutText: { color: '#DC2626', fontSize: 16, fontWeight: '700' },
});
