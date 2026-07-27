import { Info, ShieldCheck } from 'lucide-react-native';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { AppShell, Card, Header, IconButton, SectionTitle } from '@/components/common';
import { ConnectionNotice } from '@/components/ConnectionNotice';
import { MemoryItemCard } from '@/components/memory/MemoryItemCard';
import { IntegrationRow } from '@/components/settings/IntegrationRow';
import { integrations } from '@/data/mockData';
import { useAppStore } from '@/store';
import { colors, radius, typography } from '@/theme/tokens';

const categories = ['전체', '선호', '사람·관계', '프로젝트', '서비스'];

export function MemoryScreen() {
  const [category, setCategory] = useState(0);
  const memories = useAppStore((state) => state.memories);
  const { loading, error, source } = useAppStore((state) => state.memoriesLoad);
  const loadMemories = useAppStore((state) => state.loadMemories);

  useEffect(() => {
    void loadMemories(category === 0 ? undefined : categories[category]);
  }, [category, loadMemories]);

  return (
    <AppShell>
      <Header title="나의 메모리" right={<IconButton label="메모리 안내"><Info color={colors.text.secondary} size={20} /></IconButton>} />
      {source === 'mock' && error ? <ConnectionNotice message={error} /> : null}
      <View style={styles.privacy}><ShieldCheck color="#DDD6FE" size={22} /><View style={{ flex: 1 }}><Text style={styles.title}>기억은 언제든 수정·삭제할 수 있습니다.</Text><Text style={styles.sub}>민감 정보는 사용자가 승인한 경우에만 저장합니다.</Text></View></View>
      <View style={styles.chipRow} accessibilityRole="tablist">
        {categories.map((item, index) => (
          <Pressable key={item} accessibilityRole="tab" accessibilityState={{ selected: index === category }} onPress={() => setCategory(index)}>
            <Text style={[styles.chip, index === category && styles.chipActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>
      {loading ? <ActivityIndicator color={colors.text.secondary} style={styles.spinner} /> : null}
      {!loading && memories.length === 0 ? (
        <Text style={styles.empty}>아직 저장된 기억이 없습니다.</Text>
      ) : (
        memories.map((item) => <MemoryItemCard key={item.id} item={item} />)
      )}
      <SectionTitle title="연동 서비스" right={<Text style={styles.caption}>MCP</Text>} />
      <Card>{integrations.slice(0, 3).map((integration) => <IntegrationRow key={integration.id} integration={integration} />)}</Card>
    </AppShell>
  );
}
const styles = StyleSheet.create({
  privacy: { flexDirection: 'row', gap: 12, padding: 16, marginBottom: 14, borderRadius: radius.lg, backgroundColor: 'rgba(139,92,246,0.12)', borderWidth: 1, borderColor: 'rgba(139,92,246,0.32)' },
  title: { ...typography.titleSm, color: colors.text.primary },
  sub: { ...typography.caption, color: colors.text.tertiary, marginTop: 3 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 14 },
  chip: { height: 36, paddingHorizontal: 14, paddingTop: 8, borderRadius: radius.pill, backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle, color: colors.text.secondary, ...typography.labelMd, fontWeight: '800', overflow: 'hidden' },
  chipActive: { backgroundColor: colors.brand.violetSoft, color: '#DDD6FE', borderColor: 'rgba(139,92,246,0.42)' },
  caption: { ...typography.caption, color: colors.text.tertiary },
  spinner: { paddingVertical: 24 },
  empty: { ...typography.bodyMd, color: colors.text.tertiary, textAlign: 'center', paddingVertical: 32 },
});
