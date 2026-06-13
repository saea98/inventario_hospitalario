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

type Props = NativeStackScreenProps<RootStackParamList, 'Conteo'>;

export function ConteoScreen({ route, navigation }: Props) {
  const { loteUbicacionId, clave, numeroLote, cantidadSistema, fechaCaducidad } = route.params;
  const { token } = useAuth();
  const [cantidad, setCantidad] = useState(String(cantidadSistema));
  const [caducidad, setCaducidad] = useState(fechaCaducidad || '');
  const [observaciones, setObservaciones] = useState('');
  const [loading, setLoading] = useState(false);

  const guardar = async (verificar = false) => {
    if (!token) return;
    setLoading(true);
    try {
      const result = verificar
        ? await api.verificar(token, loteUbicacionId)
        : await api.conteo(token, loteUbicacionId, {
            cantidad_fisica: parseInt(cantidad, 10) || 0,
            fecha_caducidad: caducidad || undefined,
            observaciones,
          });
      Alert.alert(
        'Conteo registrado',
        `Diferencia: ${(result as { diferencia: number }).diferencia >= 0 ? '+' : ''}${
          (result as { diferencia: number }).diferencia
        }`,
        [{ text: 'OK', onPress: () => navigation.goBack() }],
      );
    } catch (error) {
      Alert.alert('Error', error instanceof Error ? error.message : 'No se pudo guardar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.clave}>{clave}</Text>
      <Text style={styles.lote}>Lote {numeroLote}</Text>
      <Text style={styles.sistema}>Cantidad en sistema: {cantidadSistema}</Text>

      <Text style={styles.label}>Cantidad física</Text>
      <TextInput
        style={styles.input}
        keyboardType="number-pad"
        value={cantidad}
        onChangeText={setCantidad}
      />

      <Text style={styles.label}>Caducidad (AAAA-MM-DD)</Text>
      <TextInput style={styles.input} value={caducidad} onChangeText={setCaducidad} />

      <Text style={styles.label}>Observaciones</Text>
      <TextInput
        style={[styles.input, styles.multiline]}
        multiline
        value={observaciones}
        onChangeText={setObservaciones}
      />

      <Pressable style={styles.secondary} onPress={() => guardar(true)} disabled={loading}>
        <Text style={styles.secondaryText}>Coincide con sistema</Text>
      </Pressable>

      <Pressable style={styles.primary} onPress={() => guardar(false)} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.primaryText}>Guardar conteo</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f8fafc' },
  clave: { fontSize: 20, fontWeight: '700', color: '#0f766e' },
  lote: { fontSize: 16, color: '#334155', marginTop: 4 },
  sistema: { color: '#64748b', marginBottom: 20 },
  label: { fontWeight: '600', marginBottom: 6, color: '#334155' },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
  },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  primary: {
    backgroundColor: '#0f766e',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  secondary: {
    borderWidth: 1,
    borderColor: '#0f766e',
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
  },
  secondaryText: { color: '#0f766e', fontWeight: '600' },
});
