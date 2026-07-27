import { Brain, Coffee, MoreHorizontal } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { IconButton, PrimaryButton, SecondaryButton, StatusPill } from '@/components/common';
import { colors, radius, typography } from '@/theme/tokens';
import type { MemoryItem } from '@/types/models';

export function MemoryItemCard({ item }: { item: MemoryItem }) {
  const Icon = item.suggested ? Brain : Coffee;
  return (
    <View style={[styles.card, item.suggested && styles.suggested]}>
      <View style={styles.icon}><Icon color="#DDD6FE" size={22} /></View>
      <View style={styles.main}>
        {item.suggested ? <StatusPill label="제안" tone="warning" /> : null}
        <Text style={[styles.title, item.suggested && styles.spaced]}>{item.title}</Text>
        <Text style={styles.content}>{item.content}</Text>
        <Text style={styles.source}>{item.source}</Text>
        {item.suggested ? <View style={styles.actions}><PrimaryButton label="저장" /><SecondaryButton label="거절" /></View> : null}
      </View>
      {!item.suggested ? <IconButton label={`${item.title} 편집`}><MoreHorizontal color={colors.text.secondary} size={20} /></IconButton> : null}
    </View>
  );
}
const styles = StyleSheet.create({
  card: { flexDirection: 'row', gap: 12, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: colors.border.subtle, borderRadius: radius.lg, backgroundColor: colors.surface.base },
  suggested: { borderColor: 'rgba(139,92,246,0.46)', backgroundColor: '#15152A' },
  icon: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.brand.violetSoft },
  main: { flex: 1, minWidth: 0 },
  title: { ...typography.titleSm, color: colors.text.primary },
  spaced: { marginTop: 8 },
  content: { ...typography.bodyMd, color: colors.text.secondary, marginTop: 4 },
  source: { ...typography.caption, color: colors.text.tertiary, marginTop: 4 },
  actions: { flexDirection: 'row', gap: 10, marginTop: 12 },
});
