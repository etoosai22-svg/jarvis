import { RefreshCw } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Header, IconButton } from '@/components/common';
import { TaskStatusCard } from '@/components/tasks/TaskStatusCard';
import { tasks } from '@/data/mockData';
import { colors, radius, typography } from '@/theme/tokens';

const segments = ['전체', '진행 중', '승인', '완료'];
export function TasksScreen() {
  return (
    <AppShell>
      <Header title="작업" right={<IconButton label="작업 새로고침"><RefreshCw color={colors.text.secondary} size={20} /></IconButton>} />
      <View style={styles.segment} accessibilityRole="tablist">{segments.map((item, index) => <Text key={item} accessibilityRole="tab" accessibilityState={{ selected: index === 0 }} style={[styles.segmentItem, index === 0 && styles.segmentActive]}>{item}</Text>)}</View>
      <View style={styles.summary}><Text style={styles.summaryTitle}>진행 중 2 · 승인 필요 1</Text><Text style={styles.summarySub}>JARVIS가 처리 중인 작업을 확인하고 승인할 수 있습니다.</Text></View>
      {tasks.map((task) => <TaskStatusCard key={task.id} task={task} />)}
    </AppShell>
  );
}
const styles = StyleSheet.create({
  segment: { flexDirection: 'row', gap: 4, height: 40, padding: 4, marginVertical: 4, borderRadius: 20, backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle },
  segmentItem: { flex: 1, textAlign: 'center', paddingTop: 6, borderRadius: 16, ...typography.caption, color: colors.text.tertiary, fontWeight: '800', overflow: 'hidden' },
  segmentActive: { backgroundColor: colors.brand.cyanSoft, color: '#BAE6FD' },
  summary: { padding: 16, marginVertical: 12, borderRadius: radius.lg, backgroundColor: 'rgba(56,189,248,0.14)', borderWidth: 1, borderColor: 'rgba(56,189,248,0.24)' },
  summaryTitle: { ...typography.titleMd, color: colors.text.primary },
  summarySub: { ...typography.bodyMd, color: colors.text.secondary, marginTop: 4 },
});
