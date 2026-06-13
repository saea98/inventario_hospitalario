import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';

import { AuthProvider, useAuth } from './src/context/AuthContext';
import { RootStackParamList } from './src/navigation/types';
import { AltaLoteScreen } from './src/screens/AltaLoteScreen';
import { ConteoScreen } from './src/screens/ConteoScreen';
import { LocationScreen } from './src/screens/LocationScreen';
import { LoginScreen } from './src/screens/LoginScreen';
import { LotesScreen } from './src/screens/LotesScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

function Navigator() {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0f766e" />
      </View>
    );
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#0f766e' },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: '600' },
      }}
    >
      {!token ? (
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
      ) : (
        <>
          <Stack.Screen name="Location" component={LocationScreen} options={{ title: 'Ubicación' }} />
          <Stack.Screen name="Lotes" component={LotesScreen} options={{ title: 'Lotes' }} />
          <Stack.Screen name="Conteo" component={ConteoScreen} options={{ title: 'Conteo' }} />
          <Stack.Screen name="AltaLote" component={AltaLoteScreen} options={{ title: 'Alta de lote' }} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <Navigator />
        <StatusBar style="light" />
      </NavigationContainer>
    </AuthProvider>
  );
}
