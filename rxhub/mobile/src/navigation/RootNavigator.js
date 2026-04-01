import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text, ActivityIndicator, View } from 'react-native';
import { useAuth } from '../context/AuthContext';

import LoginScreen from '../screens/LoginScreen';
import OTPScreen from '../screens/OTPScreen';
import DashboardScreen from '../screens/DashboardScreen';
import MedicationsScreen from '../screens/MedicationsScreen';
import RequestsScreen from '../screens/RequestsScreen';
import ResourcesScreen from '../screens/ResourcesScreen';
import ProfileScreen from '../screens/ProfileScreen';
import NewRequestScreen from '../screens/NewRequestScreen';
import RefillScreen from '../screens/RefillScreen';
import PaymentScreen from '../screens/PaymentScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const COLORS = { navy: '#1A1A2E', red: '#C8102E', orange: '#E87722' };

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.navy },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '700' },
        tabBarActiveTintColor: COLORS.red,
        tabBarInactiveTintColor: '#999',
        tabBarStyle: { paddingBottom: 6, height: 60 },
      }}
    >
      <Tab.Screen name="Home" component={DashboardScreen}
        options={{ title: 'Dashboard', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'\u25A0'}</Text> }}
      />
      <Tab.Screen name="Medications" component={MedicationsScreen}
        options={{ tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'\u2695'}</Text> }}
      />
      <Tab.Screen name="Requests" component={RequestsScreen}
        options={{ title: 'My Requests', tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'\u2709'}</Text> }}
      />
      <Tab.Screen name="Resources" component={ResourcesScreen}
        options={{ tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'\u2605'}</Text> }}
      />
      <Tab.Screen name="Profile" component={ProfileScreen}
        options={{ tabBarIcon: ({ color }) => <Text style={{ color, fontSize: 20 }}>{'\u263A'}</Text> }}
      />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.navy }}>
        <ActivityIndicator size="large" color={COLORS.red} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="NewRequest" component={NewRequestScreen}
              options={{ headerShown: true, title: 'New Request', headerStyle: { backgroundColor: COLORS.navy }, headerTintColor: '#fff' }}
            />
            <Stack.Screen name="Refill" component={RefillScreen}
              options={{ headerShown: true, title: 'Refill', headerStyle: { backgroundColor: COLORS.navy }, headerTintColor: '#fff' }}
            />
            <Stack.Screen name="Payment" component={PaymentScreen}
              options={{ headerShown: true, title: 'Payment', headerStyle: { backgroundColor: COLORS.navy }, headerTintColor: '#fff' }}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="OTP" component={OTPScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
