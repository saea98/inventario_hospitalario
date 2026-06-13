import React, { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useFocusEffect } from '@react-navigation/native';

import { api, LoteUbicacionRow } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Lotes'>;

export function LotesScreen({ route, navigation }: Props) {
  const { ubicacionId, ubicacionCodigo } = route.params;
  const { token } = useAuth();
  const [lotes, setLotes] = useState<LoteUbicacionRow[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      setLotes(await api.lotes(token, ubicacionId));
    } finally {
      setLoading(false);
    }
  }, [token, ubicacionId]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Ubicación {ubicacionCodigo}</Text>
        <Pressable
          style={styles.addButton}
          onPress={() => navigation.navigate('AltaLote', { ubicacionId, ubicacionCodigo })}
        >
          <Text style={styles.addButtonText}>+ Alta lote</Text>
        </Pressable>
      </View>

      {loading && lotes.length === 0 ? (
        <ActivityIndicator style={{ marginTop: 32 }} color="#0f766e" />
      ) : (
        <FlatList
          data={lotes}
          keyExtractor={(item) => String(item.lote_ubicacion_id)}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
          renderItem={({ item }) => (
            <Pressable
              style={styles.row}
              onPress={() =>
                navigation.navigate('Conteo', {
                  loteUbicacionId: item.lote_ubicacion_id,
                  clave: item.clave_cnis,
                  numeroLote: item.numero_lote,
                  cantidadSistema: item.cantidad_sistema,
                  fechaCaducidad: item.fecha_caducidad,
                })
              }
            >
              <Text style={styles.clave}>{item.clave_cnis}</Text>
              <Text style={styles.lote}>Lote: {item.numero_lote}</Text>
              <Text style={styles.meta}>
                Sistema: {item.cantidad_sistema}
                {item.conteo_completado ? ' · ✓ conteado' : ''}
              </Text>
            </Pressable>
          )}
          ListEmptyComponent={<Text style={styles.empty}>No hay lotes en esta ubicación</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f8fafc' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  title: { fontSize: 20, fontWeight: '700', color: '#0f172a' },
  addButton: { backgroundColor: '#0f766e', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  row: {
    backgroundColor: '#fff',
    padding: 14,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  clave: { fontWeight: '700', color: '#0f766e' },
  lote: { marginTop: 4, color: '#334155' },
  meta: { marginTop: 4, color: '#64748b' },
  empty: { textAlign: 'center', color: '#94a3b8', marginTop: 32 },
});
