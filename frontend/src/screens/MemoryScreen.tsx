import { Info, ShieldCheck } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, Header, IconButton, Row, SectionTitle } from '@/components/common';
import { MemoryItemCard } from '@/components/memory/MemoryItemCard';
import { IntegrationRow } from '@/components/settings/IntegrationRow';
import { integrations, memoryItems } from '@/data/mockData';
import { colors, radius, typography } from '@/theme/tokens';

const categories = ['선호', '사람·관계', '프로젝트', '서비스'];
export function MemoryScreen() {
  return (
    <AppShell>
      <Header title="나의 메모리" right={<IconButton label="메모리 안내"><Info color={colors.text.secondary} size={20} /></IconButton>} />
      <View style={styles.privacy}><ShieldCheck color="#DDD6FE" size={22} /><View style={{ flex: 1 }}><Text style={styles.title}>기억은 언제든 수정·삭제할 수 있습니다.</Text><Text style={styles.sub}>민감 정보는 사용자가 승인한 경우에만 저장합니다.</Text></View></View>
      <View style={styles.chipRow} accessibilityRole="tablist">{categories.map((item, index) => <Text key={item} accessibilityRole="tab" accessibilityState={{ selected: index === 0 }} style={[styles.chip, index === 0 && styles.chipActive]}>{item}</Text>)}</View>
      {memoryItems.map((item) => <MemoryItemCard key={item.id} item={item} />)}
      <SectionTitle title="연동 서비스" right={<Text style={styles.caption}>MCP</Text>} />
      <Card>{integrations.slice(0, 3).map((integration) => <IntegrationRow key={integration.id} integration={integration} />)}</Card>
    </AppShell>
  );
}
const styles = StyleSheet.create({
  privacy: { flexDirection: 'row', gap: 12, padding: 16, marginBottom: 14, borderRadius: radius.lg, backgroundColor: 'rgba(139,92,246,0.12)', borderWidth: 1, borderColor: 'rgba(139,92,246,0.32)' },
  title: { ...typography.titleSm, color: colors.text.primary },
  sub: { ...typography.caption, color: colors.text.tertiary, marginTop: 3 },
  chipRow: { flexDirection: 'row', gap: 8, marginBottom: 14 },
  chip: { height: 36, paddingHorizontal: 14, paddingTop: 8, borderRadius: radius.pill, backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle, color: colors.text.secondary, ...typography.labelMd, fontWeight: '800', overflow: 'hidden' },
  chipActive: { backgroundColor: colors.brand.violetSoft, color: '#DDD6FE', borderColor: 'rgba(139,92,246,0.42)' },
  caption: { ...typography.caption, color: colors.text.tertiary },
});
