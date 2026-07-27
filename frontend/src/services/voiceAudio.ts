/**
 * 오디오 입출력 (expo-audio / expo-file-system 의존).
 *
 * WS 프로토콜은 `voiceSession.ts`에 따로 둔다 — 그쪽은 네이티브 모듈 없이 돌아야
 * 브라우저·테스트에서 그대로 검증할 수 있다.
 */
import { createAudioPlayer, requestRecordingPermissionsAsync, setAudioModeAsync } from 'expo-audio';
import * as FileSystem from 'expo-file-system';

/** 서버가 준 media_type에 맞춰 재생 파일 확장자를 고른다. */
function extensionFor(mediaType: string | undefined): string {
  if (!mediaType) return 'm4a';
  if (mediaType.includes('aiff')) return 'aiff';
  if (mediaType.includes('mpeg')) return 'mp3';
  if (mediaType.includes('wav')) return 'wav';
  return 'm4a';
}

/**
 * base64 오디오를 파일로 떨군 뒤 재생한다.
 * expo-audio는 data: URI를 재생하지 못해 파일 경유가 필요하다.
 */
export async function playBase64Audio(audioBase64: string, mediaType?: string): Promise<void> {
  const directory = FileSystem.cacheDirectory;
  if (!directory) throw new Error('캐시 디렉터리를 사용할 수 없습니다.');

  const path = `${directory}jarvis-reply-${Date.now()}.${extensionFor(mediaType)}`;
  await FileSystem.writeAsStringAsync(path, audioBase64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  await setAudioModeAsync({ playsInSilentMode: true });
  const player = createAudioPlayer(path);
  player.play();

  const cleanup = () => {
    try {
      player.remove();
    } catch {
      /* 이미 해제됨 */
    }
    void FileSystem.deleteAsync(path, { idempotent: true });
  };
  player.addListener('playbackStatusUpdate', (status) => {
    if (status.didJustFinish) cleanup();
  });
}

export async function ensureMicrophonePermission(): Promise<boolean> {
  const permission = await requestRecordingPermissionsAsync();
  if (!permission.granted) return false;
  await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
  return true;
}

/** ArrayBuffer → base64. btoa는 문자열만 받으므로 청크로 나눠 넘긴다. */
function toBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i += 8192) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
  }
  return btoa(binary);
}

export async function readRecordingAsBase64(uri: string): Promise<string> {
  // 웹은 MediaRecorder 결과를 blob: URI로 준다 — 파일시스템으로는 읽히지 않는다.
  if (uri.startsWith('blob:') || uri.startsWith('http')) {
    const response = await fetch(uri);
    return toBase64(await response.arrayBuffer());
  }
  return FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
}
