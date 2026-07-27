import { StyleSheet, Text, View } from 'react-native';
import { GradientCard } from '@/components/common';
import { colors, typography } from '@/theme/tokens';
import type { VoiceState } from '@/types/models';

const copy: Record<VoiceState, { title: string; description: string; step: number }> = {
  idle: { title: '대기 중입니다', description: '“자비스.”라고 부르면 음성 인식을 시작합니다.', step: 1 },
  preparing: { title: '마이크를 여는 중이에요', description: '브라우저가 권한을 물으면 허용해 주세요.', step: 2 },
  listening: { title: '듣고 있어요', description: '말씀을 마치면 자동으로 분석합니다.', step: 3 },
  transcribing: { title: '음성을 이해하고 있어요', description: 'Whisper STT로 요청을 텍스트로 변환합니다.', step: 4 },
  thinking: { title: '답변을 정리하고 있어요', description: '의도를 분석하고 필요한 도구를 선택합니다.', step: 5 },
  executing: { title: '도구 실행 중입니다', description: '캘린더와 검색 MCP를 확인 중입니다.', step: 6 },
  speaking: { title: '답변 중입니다', description: 'TTS 음성과 텍스트를 함께 제공합니다.', step: 7 },
  error: { title: '연결이 불안정합니다', description: '텍스트 입력으로 다시 시도할 수 있어요.', step: 8 },
};

export function VoiceStateBanner({ state }: { state: VoiceState }) {
  const item = copy[state];
  return (
    <GradientCard style={state === 'error' ? styles.error : undefined}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.description}>{item.description}</Text>
      <View accessibilityLabel={`음성 처리 단계 8단계 중 ${item.step}단계`} style={styles.dots}>{Array.from({ length: 8 }).map((_, i) => <View key={i} style={[styles.dot, i < item.step && styles.activeDot]} />)}</View>
    </GradientCard>
  );
}

const styles = StyleSheet.create({
  title: { ...typography.titleSm, color: colors.text.primary, marginBottom: 5 },
  description: { ...typography.bodyMd, color: colors.text.secondary },
  dots: { flexDirection: 'row', gap: 6, marginTop: 12 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#334155' },
  activeDot: { backgroundColor: colors.brand.cyan },
  error: { borderColor: 'rgba(248,113,113,0.38)' },
});
