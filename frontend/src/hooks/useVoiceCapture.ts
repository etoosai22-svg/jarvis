import { RecordingPresets, useAudioRecorder } from 'expo-audio';
import { useCallback, useRef, useState } from 'react';

import { ensureMicrophonePermission, readRecordingAsBase64 } from '@/services/voiceAudio';
import { useAppStore } from '@/store';

/**
 * 마이크 한 번 눌러 말하고, 다시 눌러 보내는 흐름.
 *
 * 녹음 자체는 이 훅이 소유하고, 전송 이후(STT→도구→TTS)는 스토어가 맡는다 —
 * 화면은 `voiceState` 하나만 보면 된다.
 */
export function useVoiceCapture() {
  // 44.1kHz 스테레오는 음성 인식에 과하다. 16kHz 모노가 whisper 입력 규격이자
  // 전송량도 훨씬 작다.
  const recorder = useAudioRecorder({
    ...RecordingPresets.HIGH_QUALITY,
    sampleRate: 16000,
    numberOfChannels: 1,
  });

  const submitVoiceRecording = useAppStore((state) => state.submitVoiceRecording);
  const setVoiceState = useAppStore((state) => state.setVoiceState);
  const voiceState = useAppStore((state) => state.voiceState);

  const [permissionDenied, setPermissionDenied] = useState(false);
  // isRecording은 네이티브 상태라 렌더 사이에 지연이 있다 — 자체 플래그로 중복 탭을 막는다.
  const busy = useRef(false);

  const start = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    // 권한 요청은 몇 초가 걸린다 — 그동안 화면이 그대로면 고장난 것처럼 보인다.
    setVoiceState('preparing');
    try {
      if (!(await ensureMicrophonePermission())) {
        setPermissionDenied(true);
        setVoiceState('error');
        return;
      }
      setPermissionDenied(false);
      await recorder.prepareToRecordAsync();
      recorder.record();
      setVoiceState('listening');
    } catch {
      setVoiceState('error');
    } finally {
      busy.current = false;
    }
  }, [recorder, setVoiceState]);

  const stopAndSend = useCallback(async () => {
    if (busy.current) return;
    busy.current = true;
    try {
      await recorder.stop();
      const uri = recorder.uri;
      if (!uri) {
        setVoiceState('error');
        return;
      }
      const audioBase64 = await readRecordingAsBase64(uri);
      await submitVoiceRecording(audioBase64);
    } catch {
      setVoiceState('error');
    } finally {
      busy.current = false;
    }
  }, [recorder, setVoiceState, submitVoiceRecording]);

  /** 오브/마이크 버튼 한 곳에 물리면 되는 토글. */
  const toggle = useCallback(async () => {
    if (voiceState === 'listening') {
      await stopAndSend();
    } else if (voiceState === 'idle' || voiceState === 'error') {
      await start();
    }
    // preparing/transcribing/thinking/executing/speaking 중에는 무시 — 처리 중이다.
  }, [start, stopAndSend, voiceState]);

  return { toggle, isRecording: voiceState === 'listening', permissionDenied };
}
