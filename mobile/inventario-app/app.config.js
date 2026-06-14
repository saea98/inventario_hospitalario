/** @type {import('expo/config').ExpoConfig} */
export default ({ config }) => {
  const apiUrl =
    process.env.EXPO_PUBLIC_API_URL ||
    'https://inventarios.almacen.proyectosceib.com.mx/api/v1';

  return {
    ...config,
    name: 'Inventario Conteo',
    slug: 'inventario-app',
    version: '1.0.0',
    orientation: 'portrait',
    userInterfaceStyle: 'light',
    icon: './assets/icon.png',
    splash: {
      image: './assets/splash-icon.png',
      resizeMode: 'contain',
      backgroundColor: '#0f766e',
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: 'mx.proyectosceib.inventario.conteo',
      infoPlist: {
        ITSAppUsesNonExemptEncryption: false,
      },
    },
    android: {
      package: 'mx.proyectosceib.inventario.conteo',
      adaptiveIcon: {
        foregroundImage: './assets/adaptive-icon.png',
        backgroundColor: '#0f766e',
      },
    },
    extra: {
      apiUrl,
      eas: {
        projectId: 'cb5102fa-4c29-430b-a797-d3dbe609d16a',
      },
    },
    updates: {
      url: 'https://u.expo.dev/cb5102fa-4c29-430b-a797-d3dbe609d16a',
    },
    runtimeVersion: {
      policy: 'appVersion',
    },
    plugins: ['expo-secure-store', 'expo-updates'],
  };
};
