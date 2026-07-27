import { Bell, KeyRound, LogOut, Mic, Shield, UserRound, Volume2 } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, Header, Row, SectionTitle, StatusPill } from '@/components/common';
import { IntegrationRow } from '@/components/settings/IntegrationRow';
import { integrations } from '@/data/mockData';
import { colors, radius, typography } from '@/theme/tokens';

function SwitchMock({ on = true }: { on?: boolean }) { return <View accessibilityRole="switch" accessibilityState={{ checked: on }} style={[styles.switch, !on && styles.switchOff]}><View style={[styles.knob, !on && styles.knobOff]} /></View>; }
function Section({ title, children }: React.PropsWithChildren<{ title: string }>) { return <View style={styles.section}><SectionTitle title={title} /><Card>{children}</Card></View>; }

export function SettingsScreen() {
  return (
    <AppShell>
      <Header title="설정" />
      <View style={styles.profile}><View style={styles.avatar}><Text style={styles.avatarText}>J</Text></View><View style={{ flex: 1 }}><Text style={styles.title}>etoos 실장님</Text><Text style={styles.sub}>etoos@example.com · Pro</Text></View><StatusPill label="로그인" tone="success" /></View>
      <Section title="계정 / 보안"><Row icon={<KeyRound color={colors.brand.cyan} size={20} />} title="API Key 관리" subtitle="•••• sk-...abcd · 재인증 후 표시" right={<Text style={styles.chev}>›</Text>} /><Row icon={<Shield color={colors.brand.cyan} size={20} />} title="개인정보 / 메모리 관리" subtitle="기억 삭제 및 내보내기" right={<Text style={styles.chev}>›</Text>} /></Section>
      <Section title="음성"><Row icon={<Mic color={colors.brand.cyan} size={20} />} title="웨이크워드 활성화" subtitle="“자비스”로 호출" right={<SwitchMock />} /><Row icon={<Volume2 color={colors.brand.cyan} size={20} />} title="음성 속도" subtitle="1.0x · 한국어" right={<Text style={styles.chev}>›</Text>} /></Section>
      <Section title="MCP 서비스 연동">{integrations.slice(0, 3).map((integration) => <IntegrationRow key={integration.id} integration={integration} />)}</Section>
      <Section title="알림"><Row icon={<Bell color={colors.brand.cyan} size={20} />} title="Push 알림" subtitle="작업 완료와 승인 요청" right={<SwitchMock on={false} />} /></Section>
      <Section title="정보"><Row icon={<UserRound color={colors.brand.cyan} size={20} />} title="계정 정보" subtitle="JWT 인증 세션 활성" right={<Text style={styles.chev}>›</Text>} /><Row icon={<LogOut color={colors.semantic.error} size={20} />} title="로그아웃" subtitle="확인 후 로그아웃합니다" right={<Text style={styles.chev}>›</Text>} /></Section>
    </AppShell>
  );
}
const styles = StyleSheet.create({
  profile: { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, marginBottom: 8, borderRadius: 22, borderWidth: 1, borderColor: 'rgba(125,211,252,0.22)', backgroundColor: 'rgba(56,189,248,0.13)' },
  avatar: { width: 54, height: 54, borderRadius: 27, backgroundColor: colors.brand.cyan, alignItems: 'center', justifyContent: 'center' },
  avatarText: { ...typography.titleLg, color: colors.text.inverse, fontWeight: '900' },
  title: { ...typography.titleSm, color: colors.text.primary },
  sub: { ...typography.caption, color: colors.text.tertiary, marginTop: 3 },
  section: { marginBottom: 6 },
  switch: { width: 48, height: 30, borderRadius: radius.pill, backgroundColor: colors.brand.cyan, padding: 3, alignItems: 'flex-end' },
  switchOff: { backgroundColor: '#334155', alignItems: 'flex-start' },
  knob: { width: 24, height: 24, borderRadius: 12, backgroundColor: '#FFFFFF' },
  knobOff: {},
  chev: { color: colors.text.tertiary, fontSize: 24 },
});
