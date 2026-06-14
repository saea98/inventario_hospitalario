import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { api, Almacen, Ubicacion } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';

type Props = NativeStackScreenProps<RootStackParamList, 'Location'>;

export function LocationScreen({ navigation }: Props) {
  const { token, logout, user } = useAuth();
  const [almacenes, setAlmacenes] = useState<Almacen[]>([]);
  const [almacenId, setAlmacenId] = useState<number | null>(null);
  const [busqueda, setBusqueda] = useState('');
  const [ubicaciones, setUbicaciones] = useState<Ubicacion[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api
      .almacenes(token)
      .then((items) => {
        setAlmacenes(items);
        if (items.length === 1) {
          setAlmacenId(items[0].id);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (!token || !almacenId) {
      setUbicaciones([]);
      return;
    }
    const timer = setTimeout(() => {
      api.ubicaciones(token, almacenId, busqueda || undefined).then(setUbicaciones);
    }, 300);
    return () => clearTimeout(timer);
  }, [token, almacenId, busqueda]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0f766e" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>Hola, {user?.nombre}</Text>
        <Pressable onPress={logout}>
          <Text style={styles.link}>Salir</Text>
        </Pressable>
      </View>

      {almacenes.length === 0 ? (
        <Text style={styles.empty}>Su usuario no tiene almacén asignado. Contacte al administrador.</Text>
      ) : almacenes.length > 1 ? (
        <>
          <Text style={styles.label}>Almacén</Text>
          <FlatList
            horizontal
            data={almacenes}
            keyExtractor={(item) => String(item.id)}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chips}
            renderItem={({ item }) => (
              <Pressable
                style={[styles.chip, almacenId === item.id && styles.chipActive]}
                onPress={() => setAlmacenId(item.id)}
              >
                <Text style={[styles.chipText, almacenId === item.id && styles.chipTextActive]}>
                  {item.nombre}
                </Text>
              </Pressable>
            )}
          />
        </>
      ) : (
        <Text style={styles.almacenUnico}>Almacén: {almacenes[0]?.nombre}</Text>
      )}

      {almacenId ? (
        <>
          <TextInput
            style={styles.input}
            placeholder="Buscar ubicación (código)"
            value={busqueda}
            onChangeText={setBusqueda}
          />
          <FlatList
            data={ubicaciones}
            keyExtractor={(item) => String(item.id)}
            renderItem={({ item }) => (
              <Pressable
                style={styles.row}
                onPress={() =>
                  navigation.navigate('Lotes', {
                    ubicacionId: item.id,
                    ubicacionCodigo: item.codigo,
                  })
                }
              >
                <Text style={styles.rowTitle}>{item.codigo}</Text>
                {item.descripcion ? <Text style={styles.rowSub}>{item.descripcion}</Text> : null}
              </Pressable>
            )}
            ListEmptyComponent={<Text style={styles.empty}>Sin ubicaciones</Text>}
          />
        </>
      ) : almacenes.length > 0 ? (
        <Text style={styles.empty}>Seleccione un almacén</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f8fafc' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  greeting: { fontSize: 18, fontWeight: '600', color: '#0f172a' },
  link: { color: '#0f766e', fontWeight: '600' },
  label: { fontWeight: '600', marginBottom: 8, color: '#334155' },
  almacenUnico: { fontSize: 16, fontWeight: '600', color: '#0f766e', marginBottom: 12 },
  chips: { gap: 8, paddingBottom: 12 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#e2e8f0',
    marginRight: 8,
  },
  chipActive: { backgroundColor: '#0f766e' },
  chipText: { color: '#334155' },
  chipTextActive: { color: '#fff' },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  row: {
    backgroundColor: '#fff',
    padding: 14,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  rowTitle: { fontSize: 16, fontWeight: '600', color: '#0f172a' },
  rowSub: { color: '#64748b', marginTop: 4 },
  empty: { textAlign: 'center', color: '#94a3b8', marginTop: 24 },
});
