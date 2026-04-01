import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useAuth } from '../context/AuthContext';

export default function LoginScreen({ navigation }) {
  const [memberId, setMemberId] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, sendOtp } = useAuth();

  const handleLogin = async () => {
    if (!memberId.trim() || !phone.trim()) {
      Alert.alert('Error', 'Please enter Member ID and Phone Number');
      return;
    }
    setLoading(true);
    try {
      await login(memberId.trim(), phone.trim());
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed';
      Alert.alert('Login Failed', `${msg}\n\nWould you like to try OTP verification?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send OTP',
          onPress: async () => {
            try {
              const result = await sendOtp(memberId.trim());
              navigation.navigate('OTP', { memberId: memberId.trim(), phoneMasked: result.phone_masked });
            } catch (otpErr) {
              Alert.alert('Error', otpErr.response?.data?.detail || 'Failed to send OTP');
            }
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.inner}>
        <View style={styles.logoWrap}>
          <View style={styles.logo}><Text style={styles.logoText}>Rx</Text></View>
          <Text style={styles.title}>LeadwayHMO RxHub</Text>
          <Text style={styles.subtitle}>Member Self-Service Portal</Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Member ID</Text>
          <TextInput
            style={styles.input} value={memberId} onChangeText={setMemberId}
            placeholder="Enter your Member ID" autoCapitalize="characters"
          />

          <Text style={styles.label}>Phone Number</Text>
          <TextInput
            style={styles.input} value={phone} onChangeText={setPhone}
            placeholder="e.g. 08012345678" keyboardType="phone-pad"
          />

          <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
            <Text style={styles.buttonText}>{loading ? 'Verifying...' : 'Sign In'}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1A1A2E' },
  inner: { flex: 1, justifyContent: 'center', padding: 32 },
  logoWrap: { alignItems: 'center', marginBottom: 48 },
  logo: {
    width: 64, height: 64, borderRadius: 16, backgroundColor: '#C8102E',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  logoText: { color: '#fff', fontSize: 26, fontWeight: '700' },
  title: { color: '#fff', fontSize: 26, fontWeight: '700' },
  subtitle: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 },
  form: { backgroundColor: '#fff', borderRadius: 16, padding: 24 },
  label: { fontSize: 13, fontWeight: '600', color: '#333', marginBottom: 6, marginTop: 12 },
  input: {
    backgroundColor: '#F5F5F7', borderRadius: 10, padding: 14, fontSize: 15,
    borderWidth: 1, borderColor: '#E5E5E5',
  },
  button: {
    backgroundColor: '#C8102E', borderRadius: 10, padding: 16,
    alignItems: 'center', marginTop: 24,
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
