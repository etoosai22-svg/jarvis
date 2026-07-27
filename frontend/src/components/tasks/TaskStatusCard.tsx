import { StyleSheet, Text, View } from 'react-native';
import { PrimaryButton, SecondaryButton, StatusPill } from '@/components/common';
import { colors, radius, typography } from '@/theme/tokens';
import type { JarvisTask, TaskState } from '@/types/models';

const statusMap: Record<TaskState, { label: string; tone: 'info' | 'success' | 'warning' | 'error' | 'muted' }> = {
  queued: { label: '대기 중', tone: 'muted' }, running: { label: '검색 중', tone: 'info' }, approval_required: { label: '승인 필요', tone: 'warning' }, completed: { label: '완료', tone: 'success' }, failed: { label: '오류', tone: 'error' }, cancelled: { label: '취소됨', tone: 'muted' },
};

export function TaskStatusCard({ task }: { task: JarvisTask }) {
  const meta = statusMap[task.status];
  return (
    <View style={styles.card} accessibilityLabel={`${task.title}, ${meta.label}`}>
      <View style={styles.head}>
        <View style={styles.main}><Text style={styles.title}>{task.title}</Text><Text style={styles.subtitle}>{task.service ? `${task.service} · ` : ''}{task.subtitle}</Text></View>
        <StatusPill label={meta.label} tone={meta.tone} />
      </View>
      {typeof task.progress === 'number' ? <View style={styles.progress}><View style={[styles.fill, { width: `${task.progress}%` }, task.status === 'approval_required' && styles.warning, task.status === 'completed' && styles.success]} /></View> : null}
      {task.status === 'approval_required' ? <View style={styles.actions}><PrimaryButton label="승인" /><SecondaryButton label="취소" /></View> : null}
    </View>
  );
}
const styles = StyleSheet.create({
  card: { padding: 16, marginBottom: 12, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border.subtle, backgroundColor: colors.surface.base },
  head: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 },
  main: { flex: 1, minWidth: 0 },
  title: { ...typography.titleSm, color: colors.text.primary },
  subtitle: { ...typography.caption, color: colors.text.tertiary, marginTop: 3 },
  progress: { height: 6, borderRadius: radius.pill, backgroundColor: colors.border.subtle, marginTop: 12, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: radius.pill, backgroundColor: colors.semantic.info },
  warning: { backgroundColor: colors.semantic.warning },
  success: { backgroundColor: colors.semantic.success },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
});
