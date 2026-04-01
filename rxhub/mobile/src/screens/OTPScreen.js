import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useAuth } from '../context/AuthContext';

export default function OTPScreen({ route }) {
  const { memberId, phoneMasked } = route.params;
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const { verifyOtp } = useAuth();

  const handleVerify = async () => {
    if (otp.length < 4) {
      Alert.alert('Error', 'Please enter the complete OTP');
      return;
    }
    setLoading(true);
    try {
      await verifyOtp(memberId, otp);
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Verify OTP</Text>
        <Text style={styles.subtitle}>Enter the code sent to {phoneMasked}</Text>

        <TextInput
          style={styles.otpInput} value={otp} onChangeText={setOtp}
          placeholder="Enter OTP" keyboardType="number-pad" maxLength={6}
          textAlign="center"
        />

        <TouchableOpacity style={styles.button} onPress={handleVerify} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? 'Verifying...' : 'Verify'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1A1A2E', justifyContent: 'center', padding: 32 },
  card: { backgroundColor: '#fff', borderRadius: 16, padding: 32, alignItems: 'center' },
  title: { fontSize: 22, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#666', marginBottom: 32, textAlign: 'center' },
  otpInput: {
    backgroundColor: '#F5F5F7', borderRadius: 12, padding: 16, fontSize: 28,
    fontWeight: '700', letterSpacing: 8, width: '100%', borderWidth: 1, borderColor: '#E5E5E5',
  },
  button: {
    backgroundColor: '#C8102E', borderRadius: 10, padding: 16,
    alignItems: 'center', width: '100%', marginTop: 24,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
