/**
 * 실행 환경 설정.
 *
 * 실제 기기에서 테스트할 때는 `localhost`가 기기 자신을 가리키므로
 * 개발 PC의 LAN IP를 `.env`에 지정해야 합니다.
 *
 *   EXPO_PUBLIC_API_BASE_URL=http://192.168.0.10:8000
 */
const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export const WS_BASE_URL =
  process.env.EXPO_PUBLIC_WS_BASE_URL ?? API_BASE_URL.replace(/^http/, 'ws');

/** 백엔드가 응답하지 않을 때 목업 데이터로 화면을 채울지 여부. */
export const USE_MOCK_FALLBACK = process.env.EXPO_PUBLIC_USE_MOCK_FALLBACK !== 'false';
