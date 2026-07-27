import { ChevronLeft, Search } from 'lucide-react-native';
import { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, GradientCard, Header, IconButton, PrimaryButton, SecondaryButton, StatusPill } from '@/components/common';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { TextInputBar } from '@/components/chat/TextInputBar';
import { ConnectionNotice } from '@/components/ConnectionNotice';
import { TaskStatusCard } from '@/components/tasks/TaskStatusCard';
import { VoiceOrb } from '@/components/voice/VoiceOrb';
import { useVoiceCapture } from '@/hooks/useVoiceCapture';
import { useAppStore } from '@/store';
import { colors, radius, typography } from '@/theme/tokens';
import type { VoiceState } from '@/types/models';

const STATE_COPY: Record<VoiceState, { title: string; sub: string }> = {
  idle: { title: '무엇을 도와드릴까요?', sub: '텍스트로 입력하거나 마이크를 눌러 말씀하세요' },
  listening: { title: '듣고 있습니다', sub: '말씀이 끝나면 자동으로 인식합니다' },
  transcribing: { title: '음성을 인식하고 있습니다', sub: '잠시만 기다려 주세요' },
  thinking: { title: '요청을 정리하고 있습니다', sub: '응답을 준비하는 중입니다' },
  executing: { title: '작업을 실행하고 있습니다', sub: 'MCP 실행 · 응답을 정리하고 있어요' },
  speaking: { title: '답변하고 있습니다', sub: '음성 재생 중입니다' },
  error: { title: '요청을 처리하지 못했습니다', sub: '연결 상태를 확인한 뒤 다시 시도해 주세요' },
};

export function ConversationScreen() {
  const messages = useAppStore((state) => state.messages);
  const voiceState = useAppStore((state) => state.voiceState);
  const chat = useAppStore((state) => state.chat);
  const sendMessage = useAppStore((state) => state.sendMessage);
  const { toggle: toggleVoice, permissionDenied } = useVoiceCapture();
  const tasks = useAppStore((state) => state.tasks);
  const loadTasks = useAppStore((state) => state.loadTasks);
  const setTaskState = useAppStore((state) => state.setTaskState);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  const runningTask = tasks.find((task) => task.status === 'running' || task.status === 'queued');
  const approvalTask = tasks.find((task) => task.status === 'approval_required');
  const copy = STATE_COPY[voiceState];

  return (
    <AppShell>
      <Header title="오늘 대화" left={<IconButton label="이전 화면으로 돌아가기"><ChevronLeft color={colors.text.secondary} size={22} /></IconButton>} right={<IconButton label="대화 검색"><Search color={colors.text.secondary} size={20} /></IconButton>} />
      <GradientCard style={styles.compactPanel}>
        <VoiceOrb state={voiceState} compact onPress={() => void toggleVoice()} />
        <View style={styles.flex}><Text style={styles.title}>{copy.title}</Text><Text style={styles.sub}>{copy.sub}</Text></View>
        <StatusPill label={voiceState} tone={voiceState === 'error' ? 'error' : 'info'} />
      </GradientCard>
      {permissionDenied ? (
        <ConnectionNotice message="마이크 권한이 필요합니다. 설정에서 허용한 뒤 다시 시도해 주세요." />
      ) : chat.error ? (
        <ConnectionNotice message={chat.error} />
      ) : null}
      <View style={styles.messageList}>{messages.map((message) => <MessageBubble key={message.id} message={message} />)}</View>
      {runningTask ? <TaskStatusCard task={runningTask} /> : null}
      {approvalTask ? (
        <Card style={styles.approvalCard}>
          <StatusPill label="승인 필요" tone="warning" />
          <Text style={[styles.title, styles.approvalTitle]}>{approvalTask.title}</Text>
          <Text style={styles.sub}>{approvalTask.subtitle}</Text>
          <View style={styles.actions}>
            <PrimaryButton label="승인하고 실행" onPress={() => void setTaskState(approvalTask.id, 'running')} />
            <SecondaryButton label="취소" onPress={() => void setTaskState(approvalTask.id, 'cancelled')} />
          </View>
        </Card>
      ) : null}
      <TextInputBar
        onSend={(text) => void sendMessage(text)}
        onVoicePress={() => void toggleVoice()}
        sending={chat.loading}
      />
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
