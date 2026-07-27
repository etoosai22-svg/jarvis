import { LinearGradient } from 'expo-linear-gradient';
import { PropsWithChildren, ReactNode } from 'react';
import { Pressable, ScrollView, StyleProp, StyleSheet, Text, View, ViewStyle } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, radius, shadow, spacing, typography } from '@/theme/tokens';

export function AppShell({ children, scroll = true }: PropsWithChildren<{ scroll?: boolean }>) {
  const insets = useSafeAreaInsets();
  const content = <View style={[styles.shellContent, { paddingBottom: 96 + insets.bottom }]}>{children}</View>;
  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
      <LinearGradient colors={[colors.bg.depth, colors.bg.app]} style={StyleSheet.absoluteFill} />
      {scroll ? <ScrollView showsVerticalScrollIndicator={false}>{content}</ScrollView> : content}
    </SafeAreaView>
  );
}

export function Header({ title, left, right }: { title: string; left?: ReactNode; right?: ReactNode }) {
  return (
    <View style={styles.header} accessible accessibilityRole="header">
      <View style={styles.headerSide}>{left}</View>
      <Text style={styles.headerTitle}>{title}</Text>
      <View style={[styles.headerSide, styles.headerRight]}>{right}</View>
    </View>
  );
}

export function IconButton({ label, children, onPress }: PropsWithChildren<{ label: string; onPress?: () => void }>) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={({ pressed }) => [styles.iconButton, pressed && styles.pressed]}>
      {children}
    </Pressable>
  );
}

export function Card({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function GradientCard({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return (
    <LinearGradient colors={['rgba(56,189,248,0.18)', 'rgba(139,92,246,0.14)']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.card, styles.gradientCard, style]}>
      {children}
    </LinearGradient>
  );
}

export function SectionTitle({ title, right }: { title: string; right?: ReactNode }) {
  return (
    <View style={styles.sectionTitle}>
      <Text style={styles.sectionTitleText}>{title}</Text>
      {right}
    </View>
  );
}

export function StatusPill({ label, tone = 'info' }: { label: string; tone?: 'info' | 'success' | 'warning' | 'error' | 'muted' }) {
  const toneStyle = {
    info: { backgroundColor: 'rgba(96,165,250,0.16)', color: '#BFDBFE' },
    success: { backgroundColor: colors.semantic.successBg, color: '#86EFAC' },
    warning: { backgroundColor: colors.semantic.warningBg, color: '#FCD34D' },
    error: { backgroundColor: colors.semantic.errorBg, color: '#FCA5A5' },
    muted: { backgroundColor: 'rgba(148,163,184,0.13)', color: colors.text.secondary },
  }[tone];
  return <Text style={[styles.statusPill, { backgroundColor: toneStyle.backgroundColor, color: toneStyle.color }]}>{label}</Text>;
}

export function Row({ icon, title, subtitle, right }: { icon: ReactNode; title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <View style={styles.row}>
      <View style={styles.iconBox}>{icon}</View>
      <View style={styles.rowMain}>
        <Text numberOfLines={1} style={styles.rowTitle}>{title}</Text>
        {subtitle ? <Text numberOfLines={2} style={styles.rowSub}>{subtitle}</Text> : null}
      </View>
      {right}
    </View>
  );
}

export function PrimaryButton({ label, onPress }: { label: string; onPress?: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}><Text style={styles.primaryButtonText}>{label}</Text></Pressable>;
}

export function SecondaryButton({ label, onPress }: { label: string; onPress?: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress} style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}><Text style={styles.secondaryButtonText}>{label}</Text></Pressable>;
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: colors.bg.app },
  shellContent: { paddingHorizontal: spacing[16], paddingTop: spacing[8] },
  header: { height: 56, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing[12] },
  headerSide: { width: 52, alignItems: 'flex-start' },
  headerRight: { alignItems: 'flex-end' },
  headerTitle: { ...typography.titleMd, color: colors.text.primary, textAlign: 'center', flex: 1 },
  iconButton: { minWidth: 44, minHeight: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(17,24,39,0.62)', borderWidth: 1, borderColor: colors.border.subtle },
  pressed: { opacity: 0.72 },
  card: { padding: 16, borderRadius: radius.lg, backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle, ...shadow.card },
  gradientCard: { borderColor: 'rgba(125,211,252,0.22)' },
  sectionTitle: { marginTop: 22, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sectionTitleText: { ...typography.titleSm, color: colors.text.primary },
  statusPill: { minHeight: 28, paddingHorizontal: 10, paddingVertical: 6, borderRadius: radius.pill, ...typography.caption, fontWeight: '700', overflow: 'hidden' },
  row: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: 'rgba(36,48,71,0.75)' },
  iconBox: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(56,189,248,0.13)' },
  rowMain: { flex: 1, minWidth: 0 },
  rowTitle: { ...typography.bodyMd, fontWeight: '700', color: colors.text.primary },
  rowSub: { ...typography.caption, color: colors.text.tertiary, marginTop: 2 },
  primaryButton: { height: 44, borderRadius: 14, backgroundColor: colors.brand.cyan, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14, flex: 1 },
  primaryButtonText: { ...typography.labelMd, color: colors.text.inverse, fontWeight: '800' },
  secondaryButton: { height: 44, borderRadius: 14, borderWidth: 1, borderColor: colors.border.subtle, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14, flex: 1 },
  secondaryButtonText: { ...typography.labelMd, color: colors.text.secondary, fontWeight: '800' },
});
