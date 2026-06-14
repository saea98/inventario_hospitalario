import Constants from 'expo-constants';

function resolveApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '');
  if (fromEnv) return fromEnv;

  const fromExtra = (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl?.replace(
    /\/$/,
    '',
  );
  if (fromExtra) return fromExtra;

  return 'http://localhost:8700/api/v1';
}

const API_URL = resolveApiUrl();

type RequestOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (data as { detail?: string }).detail || 'Error en la solicitud';
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return data as T;
}

export type LoginResponse = {
  access_token: string;
  user_id: number;
  username: string;
  nombre: string;
};

export type Almacen = { id: number; nombre: string; codigo: string };
export type Ubicacion = { id: number; codigo: string; descripcion?: string };
export type LoteUbicacionRow = {
  lote_ubicacion_id: number;
  clave_cnis: string;
  descripcion: string;
  numero_lote: string;
  fecha_caducidad: string | null;
  cantidad_sistema: number;
  conteo_completado: boolean;
};

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { username, password },
    }),

  almacenes: (token: string) => request<Almacen[]>('/conteos/almacenes', { token }),

  ubicaciones: (token: string, almacenId: number, q?: string) => {
    const params = new URLSearchParams({ almacen_id: String(almacenId) });
    if (q) params.set('q', q);
    return request<Ubicacion[]>(`/conteos/ubicaciones?${params}`, { token });
  },

  lotes: (token: string, ubicacionId: number) =>
    request<LoteUbicacionRow[]>(`/conteos/ubicaciones/${ubicacionId}/lotes`, { token }),

  conteo: (
    token: string,
    loteUbicacionId: number,
    payload: { cantidad_fisica: number; fecha_caducidad?: string; observaciones?: string },
  ) =>
    request(`/conteos/lotes/${loteUbicacionId}/conteo`, {
      method: 'POST',
      token,
      body: payload,
    }),

  verificar: (token: string, loteUbicacionId: number) =>
    request(`/conteos/lotes/${loteUbicacionId}/verificar`, {
      method: 'POST',
      token,
    }),

  altaLote: (
    token: string,
    ubicacionId: number,
    payload: {
      clave_cnis: string;
      numero_lote: string;
      cantidad_inicial: number;
      fecha_caducidad: string;
      observaciones?: string;
    },
  ) =>
    request(`/conteos/ubicaciones/${ubicacionId}/lotes`, {
      method: 'POST',
      token,
      body: payload,
    }),
};
