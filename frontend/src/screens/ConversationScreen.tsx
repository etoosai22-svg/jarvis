import { ChevronLeft, Search } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, GradientCard, Header, IconButton, PrimaryButton, SecondaryButton, StatusPill } from '@/components/common';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { TextInputBar } from '@/components/chat/TextInputBar';
import { TaskStatusCard } from '@/components/tasks/TaskStatusCard';
import { VoiceOrb } from '@/components/voice/VoiceOrb';
import { messages, tasks } from '@/data/mockData';
import { colors, radius, typography } from '@/theme/tokens';

export function ConversationScreen() {
  const runningTask = tasks[0];
  return (
    <AppShell>
      <Header title="오늘 대화" left={<IconButton label="이전 화면으로 돌아가기"><ChevronLeft color={colors.text.secondary} size={22} /></IconButton>} right={<IconButton label="대화 검색"><Search color={colors.text.secondary} size={20} /></IconButton>} />
      <GradientCard style={styles.compactPanel}>
        <VoiceOrb state="executing" compact />
        <View style={styles.flex}><Text style={styles.title}>자료 검색 중입니다</Text><Text style={styles.sub}>Search MCP 실행 · 응답을 정리하고 있어요</Text></View>
        <StatusPill label="executing" tone="info" />
      </GradientCard>
      <View style={styles.messageList}>{messages.slice(0, 2).map((message) => <MessageBubble key={message.id} message={message} />)}</View>
      <TaskStatusCard task={runningTask} />
      <MessageBubble message={messages[2]} />
      <Card style={styles.approvalCard}>
        <StatusPill label="승인 필요" tone="warning" />
        <Text style={[styles.title, styles.approvalTitle]}>회의 참석자에게 요약 메일을 보낼까요?</Text>
        <Text style={styles.sub}>대상: 전략회의 참석자 5명 · 첨부: 요약 노트</Text>
        <View style={styles.actions}><PrimaryButton label="승인하고 실행" /><SecondaryButton label="취소" /></View>
      </Card>
      <TextInputBar />
    </AppShell>
  );
}
const styles = StyleSheet.create({
  compactPanel: { flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 12, borderRadius: 22 },
  flex: { flex: 1, minWidth: 0 },
  title: { ...typography.titleSm, color: colors.text.primary },
  sub: { ...typography.caption, color: colors.text.tertiary, marginTop: 2 },
  messageList: { gap: 8, marginBottom: 8 },
  approvalCard: { backgroundColor: colors.surface.raised, borderColor: 'rgba(245,158,11,0.36)', borderRadius: radius.lg },
  approvalTitle: { marginTop: 10 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
});
