import { LinearGradient } from 'expo-linear-gradient';
import { Mic, Volume2, AlertTriangle, Loader, Search, CheckCircle2 } from 'lucide-react-native';
import { useEffect, useRef } from 'react';
import { AccessibilityInfo, Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, shadow, size, typography } from '@/theme/tokens';
import type { VoiceState } from '@/types/models';

const labels: Record<VoiceState, string> = {
  idle: '자비스 또는 탭',
  listening: '듣고 있어요',
  transcribing: '음성을 이해하고 있어요',
  thinking: '답변을 정리 중입니다',
  executing: '도구 실행 중입니다',
  speaking: '답변 중입니다',
  error: '다시 시도해 주세요',
};

export function VoiceOrb({ state = 'idle', compact = false, onPress }: { state?: VoiceState; compact?: boolean; onPress?: () => void }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    AccessibilityInfo.announceForAccessibility(labels[state]);
    const loop = Animated.loop(Animated.timing(pulse, { toValue: 1, duration: state === 'speaking' ? 900 : 1400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }));
    pulse.setValue(0);
    loop.start();
    return () => loop.stop();
  }, [state, pulse]);

  const scale = pulse.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0.98, state === 'listening' ? 1.08 : 1.04, 0.98] });
  const Icon = state === 'speaking' ? Volume2 : state === 'error' ? AlertTriangle : state === 'thinking' || state === 'transcribing' ? Loader : state === 'executing' ? Search : state === 'idle' ? Mic : CheckCircle2;
  const dim = compact ? size.orbCompact : size.orb;
  return (
    <View style={[styles.wrapper, compact && styles.compactWrapper]}>
      <Animated.View style={[styles.halo, compact && styles.compactHalo, { transform: [{ scale }] }]} />
      <Pressable accessibilityRole="button" accessibilityLabel="자비스 음성 호출" accessibilityHint="두 번 탭하면 음성 인식을 시작하거나 중지합니다" accessibilityState={{ busy: state !== 'idle' }} onPress={onPress} style={({ pressed }) => [{ width: dim, height: dim, borderRadius: dim / 2 }, pressed && { opacity: 0.72 }]}>
        <LinearGradient colors={state === 'error' ? [colors.semantic.error, colors.semantic.errorBg] : [colors.brand.cyan, colors.brand.violet]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.core, { width: dim, height: dim, borderRadius: dim / 2 }]}>
          {state === 'listening' ? <WaveBars dark /> : <Icon color={colors.text.inverse} size={compact ? 30 : 40} strokeWidth={2.4} />}
        </LinearGradient>
      </Pressable>
      {!compact ? <Text style={styles.label}>{labels[state]}</Text> : null}
    </View>
  );
}

export function WaveBars({ dark = false }: { dark?: boolean }) {
  const bars = [16, 30, 42, 24, 34];
  return <View style={styles.wave}>{bars.map((h, i) => <View key={i} style={[styles.bar, { height: h, backgroundColor: dark ? colors.text.inverse : colors.brand.cyan }]} />)}</View>;
}

const styles = StyleSheet.create({
  wrapper: { minHeight: 260, alignItems: 'center', justifyContent: 'center' },
  compactWrapper: { minHeight: 82 },
  halo: { position: 'absolute', width: 230, height: 230, borderRadius: 115, backgroundColor: 'rgba(56,189,248,0.12)', borderWidth: 1, borderColor: 'rgba(125,211,252,0.32)' },
  compactHalo: { width: 128, height: 128, borderRadius: 64 },
  core: { alignItems: 'center', justifyContent: 'center', ...shadow.orb },
  label: { marginTop: 14, ...typography.labelMd, color: colors.text.secondary },
  wave: { height: 48, flexDirection: 'row', alignItems: 'center', gap: 4 },
  bar: { width: 5, borderRadius: radius.pill },
});
