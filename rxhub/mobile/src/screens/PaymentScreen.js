import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView, Linking } from 'react-native';
import api from '../services/api';

const PAYMENT_TYPES = ['UNCOVERED_MEDICATION', 'SUPPLEMENT', 'COPAY', 'TOP_UP'];

export default function PaymentScreen({ navigation }) {
  const [amount, setAmount] = useState('');
  const [paymentType, setPaymentType] = useState('UNCOVERED_MEDICATION');
  const [loading, setLoading] = useState(false);

  const handlePay = async () => {
    const numAmount = parseFloat(amount);
    if (!numAmount || numAmount <= 0) {
      Alert.alert('Error', 'Please enter a valid amount');
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post('/payments/initiate', {
        amount: numAmount,
        payment_type: paymentType,
      });

      if (data.authorization_url) {
        Alert.alert(
          'Proceed to Payment',
          'You will be redirected to the payment gateway.',
          [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Pay Now',
              onPress: () => Linking.openURL(data.authorization_url),
            },
          ]
        );
      }
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Payment initiation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <View style={styles.card}>
        <Text style={styles.title}>Make a Payment</Text>
        <Text style={styles.subtitle}>Pay for uncovered medications, supplements, or copays</Text>

        <Text style={styles.label}>Payment Type</Text>
        <View style={styles.typeGrid}>
          {PAYMENT_TYPES.map(t => (
            <TouchableOpacity
              key={t}
              style={[styles.typeBtn, paymentType === t && styles.typeBtnActive]}
              onPress={() => setPaymentType(t)}
            >
              <Text style={[styles.typeBtnText, paymentType === t && styles.typeBtnTextActive]}>
                {t.replace(/_/g, ' ')}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Amount (NGN)</Text>
        <TextInput
          style={styles.amountInput}
          placeholder="0.00"
          value={amount}
          onChangeText={setAmount}
          keyboardType="decimal-pad"
        />

        <TouchableOpacity style={styles.payBtn} onPress={handlePay} disabled={loading}>
          <Text style={styles.payBtnText}>{loading ? 'Processing...' : 'Proceed to Pay'}</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.info}>
        <Text style={styles.infoTitle}>Secure Payment</Text>
        <Text style={styles.infoText}>Payments are processed securely via Paystack. Your card details are never stored on our servers.</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F5F7' },
  card: { backgroundColor: '#fff', borderRadius: 14, padding: 24, shadowColor: '#000', shadowOpacity: 0.04, shadowOffset: { width: 0, height: 2 }, shadowRadius: 8, elevation: 2 },
  title: { fontSize: 20, fontWeight: '700', color: '#1A1A2E' },
  subtitle: { fontSize: 13, color: '#666', marginTop: 4, marginBottom: 20 },
  label: { fontSize: 13, fontWeight: '700', color: '#333', marginTop: 16, marginBottom: 8 },
  typeGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  typeBtn: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10, backgroundColor: '#F5F5F7', borderWidth: 1, borderColor: '#E5E5E5' },
  typeBtnActive: { backgroundColor: '#1A1A2E', borderColor: '#1A1A2E' },
  typeBtnText: { fontSize: 12, fontWeight: '600', color: '#666' },
  typeBtnTextActive: { color: '#fff' },
  amountInput: { backgroundColor: '#F5F5F7', borderRadius: 12, padding: 16, fontSize: 24, fontWeight: '700', textAlign: 'center', borderWidth: 1, borderColor: '#E5E5E5' },
  payBtn: { backgroundColor: '#C8102E', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 24 },
  payBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  info: { marginTop: 24, padding: 16 },
  infoTitle: { fontSize: 14, fontWeight: '700', color: '#1A1A2E' },
  infoText: { fontSize: 13, color: '#666', marginTop: 4, lineHeight: 20 },
});
