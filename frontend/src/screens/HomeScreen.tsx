import { Settings } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, Header, IconButton, Row, SectionTitle, StatusPill } from '@/components/common';
import { VoiceOrb } from '@/components/voice/VoiceOrb';
import { VoiceStateBanner } from '@/components/voice/VoiceStateBanner';
import { recentConversations, todaySchedules } from '@/data/mockData';
import { colors, typography } from '@/theme/tokens';

export function HomeScreen() {
  return (
    <AppShell>
      <Header title="JARVIS" right={<IconButton label="설정 열기"><Settings color={colors.text.secondary} size={21} /></IconButton>} />
      <View style={styles.heroBlock}>
        <Text style={styles.hero}>안녕하세요,{`\n`}실장님.</Text>
        <Text style={styles.subtitle}>무엇을 도와드릴까요?</Text>
      </View>
      <VoiceOrb state="idle" />
      <VoiceStateBanner state="idle" />
      <SectionTitle title="오늘 일정" right={<StatusPill label="3개" tone="info" />} />
      <Card>{todaySchedules.map((item) => <Row key={item.time} icon={<Text style={styles.time}>{item.time}</Text>} title={item.title} subtitle={item.meta} />)}</Card>
      <SectionTitle title="최근 대화" right={<Text style={styles.caption}>최근 3개</Text>} />
      <Card>{recentConversations.map((item) => <Row key={item.title} icon={<Text>{item.icon}</Text>} title={item.title} subtitle={item.meta} />)}</Card>
    </AppShell>
  );
}
const styles = StyleSheet.create({
  heroBlock: { marginBottom: 20 },
  hero: { ...typography.hero, color: colors.text.primary },
  subtitle: { ...typography.bodyLg, color: colors.text.secondary, marginTop: 6 },
  time: { ...typography.caption, color: '#BAE6FD', fontWeight: '800' },
  caption: { ...typography.caption, color: colors.text.tertiary },
});
