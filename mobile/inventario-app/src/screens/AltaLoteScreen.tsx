import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'AltaLote'>;

export function AltaLoteScreen({ route, navigation }: Props) {
  const { ubicacionId, ubicacionCodigo } = route.params;
  const { token } = useAuth();
  const [clave, setClave] = useState('');
  const [numeroLote, setNumeroLote] = useState('');
  const [cantidad, setCantidad] = useState('0');
  const [caducidad, setCaducidad] = useState('');
  const [loading, setLoading] = useState(false);

  const guardar = async () => {
    if (!token || !clave.trim() || !numeroLote.trim() || !caducidad) {
      Alert.alert('Datos incompletos', 'Clave, lote, cantidad y caducidad son obligatorios.');
      return;
    }
    setLoading(true);
    try {
      await api.altaLote(token, ubicacionId, {
        clave_cnis: clave.trim(),
        numero_lote: numeroLote.trim(),
        cantidad_inicial: parseInt(cantidad, 10) || 0,
        fecha_caducidad: caducidad,
      });
      Alert.alert('Listo', 'Lote dado de alta', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'No se pudo crear el lote');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Alta en {ubicacionCodigo}</Text>

      <Text style={styles.label}>Clave CNIS</Text>
      <TextInput style={styles.input} value={clave} onChangeText={setClave} autoCapitalize="characters" />

      <Text style={styles.label}>Número de lote</Text>
      <TextInput style={styles.input} value={numeroLote} onChangeText={setNumeroLote} />

      <Text style={styles.label}>Cantidad inicial</Text>
      <TextInput style={styles.input} keyboardType="number-pad" value={cantidad} onChangeText={setCantidad} />

      <Text style={styles.label}>Caducidad (AAAA-MM-DD)</Text>
      <TextInput style={styles.input} value={caducidad} onChangeText={setCaducidad} placeholder="2026-12-31" />

      <Pressable style={styles.button} onPress={guardar} disabled={loading}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Crear lote</Text>}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f8fafc' },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 16, color: '#0f172a' },
  label: { fontWeight: '600', marginBottom: 6, color: '#334155' },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  button: {
    backgroundColor: '#0f766e',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});
