import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, typography } from '@/theme/tokens';
import type { Message } from '@/types/models';

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <View style={[styles.bubble, isUser ? styles.user : styles.assistant, message.partial && styles.partial]}>
      {!isUser ? <Text style={styles.label}>JARVIS</Text> : null}
      <Text style={[styles.text, isUser && styles.userText]}>{message.content}{message.streaming ? '  ●' : ''}</Text>
    </View>
  );
}
const styles = StyleSheet.create({
  bubble: { maxWidth: '84%', paddingHorizontal: 16, paddingVertical: 14, borderRadius: radius.lg, marginVertical: 4 },
  assistant: { alignSelf: 'flex-start', backgroundColor: colors.surface.base, borderWidth: 1, borderColor: colors.border.subtle, borderBottomLeftRadius: 6 },
  user: { alignSelf: 'flex-end', backgroundColor: colors.brand.cyanDeep, borderBottomRightRadius: 6 },
  partial: { opacity: 0.72 },
  label: { ...typography.caption, color: colors.brand.cyan, fontWeight: '800', marginBottom: 4 },
  text: { ...typography.bodyLg, color: colors.text.primary },
  userText: { color: '#FFFFFF' },
});
