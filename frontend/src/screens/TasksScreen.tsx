import { RefreshCw } from 'lucide-react-native';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { AppShell, Header, IconButton } from '@/components/common';
import { ConnectionNotice } from '@/components/ConnectionNotice';
import { TaskStatusCard } from '@/components/tasks/TaskStatusCard';
import { useAppStore } from '@/store';
import { colors, radius, typography } from '@/theme/tokens';
import type { TaskState } from '@/types/models';

const segments: { label: string; match: TaskState[] | null }[] = [
  { label: '전체', match: null },
  { label: '진행 중', match: ['queued', 'running'] },
  { label: '승인', match: ['approval_required'] },
  { label: '완료', match: ['completed'] },
];

export function TasksScreen() {
  const [segment, setSegment] = useState(0);
  const tasks = useAppStore((state) => state.tasks);
  const { loading, error, source } = useAppStore((state) => state.tasksLoad);
  const loadTasks = useAppStore((state) => state.loadTasks);
  const setTaskState = useAppStore((state) => state.setTaskState);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  const visibleTasks = useMemo(() => {
    const match = segments[segment].match;
    return match ? tasks.filter((task) => match.includes(task.status)) : tasks;
  }, [segment, tasks]);

  const runningCount = tasks.filter((task) => task.status === 'running' || task.status === 'queued').length;
  const approvalCount = tasks.filter((task) => task.status === 'approval_required').length;

  return (
    <AppShell>
      <Header
        title="작업"
        right={
          <IconButton label="작업 새로고침" onPress={() => void loadTasks()}>
            {loading ? <ActivityIndicator color={colors.text.secondary} size="small" /> : <RefreshCw color={colors.text.secondary} size={20} />}
          </IconButton>
        }
      />
      {source === 'mock' && error ? <ConnectionNotice message={error} /> : null}
      <View style={styles.segment} accessibilityRole="tablist">
        {segments.map((item, index) => (
          <Pressable key={item.label} accessibilityRole="tab" accessibilityState={{ selected: index === segment }} onPress={() => setSegment(index)} style={styles.segmentPress}>
            <Text style={[styles.segmentItem, index === segment && styles.segmentActive]}>{item.label}</Text>
          </Pressable>
        ))}
      </View>
      <View style={styles.summary}>
        <Text style={styles.summaryTitle}>진행 중 {runningCount} · 승인 필요 {approvalCount}</Text>
        <Text style={styles.summarySub}>JARVIS가 처리 중인 작업을 확인하고 승인할 수 있습니다.</Text>
      </View>
      {visibleTasks.length === 0 && !loading ? (
        <Text style={styles.empty}>표시할 작업이 없습니다.</Text>
      ) : (
        visibleTasks.map((task) => (
          <TaskStatusCard
            key={task.id}
            task={task}
            onApprove={() => void setTaskState(task.id, 'running')}
            onCancel={() => void setTaskState(task.id, 'cancelled')}
          />
        ))
      )}
    </AppShell>
  );
}
const styles = StyleSheet.create({
  segment: { flexDirection: 'row', gap: 4, height: 40, padding: 4, marginVertical: 4, borderRadius: 20, backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle },
  segmentPress: { flex: 1 },
  segmentItem: { textAlign: 'center', paddingTop: 6, borderRadius: 16, ...typography.caption, color: colors.text.tertiary, fontWeight: '800', overflow: 'hidden' },
  segmentActive: { backgroundColor: colors.brand.cyanSoft, color: '#BAE6FD' },
  summary: { padding: 16, marginVertical: 12, borderRadius: radius.lg, backgroundColor: 'rgba(56,189,248,0.14)', borderWidth: 1, borderColor: 'rgba(56,189,248,0.24)' },
  summaryTitle: { ...typography.titleMd, color: colors.text.primary },
  summarySub: { ...typography.bodyMd, color: colors.text.secondary, marginTop: 4 },
  empty: { ...typography.bodyMd, color: colors.text.tertiary, textAlign: 'center', paddingVertical: 32 },
});
