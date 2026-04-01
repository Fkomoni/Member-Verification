import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';

export default function PaymentScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.card}>
        <View style={styles.iconWrap}>
          <Text style={styles.icon}>{'\u26A1'}</Text>
        </View>
        <Text style={styles.title}>Payments</Text>
        <Text style={styles.subtitle}>Coming Soon</Text>
        <Text style={styles.body}>
          We're working on a secure payment feature that will allow you to pay for uncovered medications, nutritional supplements, and copays directly from the app.
        </Text>

        <View style={styles.features}>
          <Feature text="Pay for uncovered medications" />
          <Feature text="Purchase nutritional supplements" />
          <Feature text="Manage copay payments" />
          <Feature text="Secure payment via Paystack" />
          <Feature text="Full payment history" />
        </View>

        <View style={styles.notifyBox}>
          <Text style={styles.notifyText}>You'll be notified when this feature becomes available.</Text>
        </View>
      </View>
    </ScrollView>
  );
}

function Feature({ text }) {
  return (
    <View style={styles.featureRow}>
      <View style={styles.featureDot} />
      <Text style={styles.featureText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  content: { padding: 16, paddingBottom: 40 },
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 32,
    alignItems: 'center', shadowColor: '#000', shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2,
  },
  iconWrap: {
    width: 72, height: 72, borderRadius: 36, backgroundColor: '#FFF7ED',
    justifyContent: 'center', alignItems: 'center', marginBottom: 20,
  },
  icon: { fontSize: 32 },
  title: { fontSize: 24, fontWeight: '700', color: '#1A1A2E' },
  subtitle: {
    fontSize: 14, fontWeight: '700', color: '#E87722',
    textTransform: 'uppercase', letterSpacing: 1, marginTop: 4, marginBottom: 16,
  },
  body: { fontSize: 14, color: '#666', textAlign: 'center', lineHeight: 22, marginBottom: 24 },
  features: { width: '100%', marginBottom: 24 },
  featureRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8 },
  featureDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#C8102E', marginRight: 12 },
  featureText: { fontSize: 14, color: '#333' },
  notifyBox: {
    backgroundColor: '#F0F4FF', borderRadius: 12, padding: 16, width: '100%', alignItems: 'center',
  },
  notifyText: { fontSize: 13, color: '#2563EB', fontWeight: '500', textAlign: 'center' },
});
