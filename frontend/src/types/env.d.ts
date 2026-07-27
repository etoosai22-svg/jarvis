/**
 * Expo는 `EXPO_PUBLIC_*` 환경변수를 번들 시점에 `process.env`로 치환한다.
 * @types/node를 끌어오지 않기 위해 필요한 키만 선언한다.
 */
declare const process: {
  env: {
    EXPO_PUBLIC_API_BASE_URL?: string;
    EXPO_PUBLIC_WS_BASE_URL?: string;
    EXPO_PUBLIC_USE_MOCK_FALLBACK?: string;
  };
};

/** Expo/React Native가 번들 시점에 주입하는 개발 모드 플래그. */
declare const __DEV__: boolean;
