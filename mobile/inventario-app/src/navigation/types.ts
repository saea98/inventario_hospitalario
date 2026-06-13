export type RootStackParamList = {
  Login: undefined;
  Location: undefined;
  Lotes: { ubicacionId: number; ubicacionCodigo: string };
  Conteo: {
    loteUbicacionId: number;
    clave: string;
    numeroLote: string;
    cantidadSistema: number;
    fechaCaducidad: string | null;
  };
  AltaLote: { ubicacionId: number; ubicacionCodigo: string };
};
