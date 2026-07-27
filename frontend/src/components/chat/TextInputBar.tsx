import { Mic, Send } from 'lucide-react-native';
import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';
import { colors, radius, typography } from '@/theme/tokens';

export function TextInputBar() {
  const [text, setText] = useState('');
  return (
    <View style={styles.bar}>
      <TextInput accessibilityLabel="요청 입력" placeholder="텍스트로 요청하기" placeholderTextColor={colors.text.tertiary} value={text} onChangeText={setText} multiline style={styles.input} />
      <Pressable accessibilityRole="button" accessibilityLabel={text ? '요청 전송' : '음성 입력 시작'} style={styles.button}>{text ? <Send color={colors.text.inverse} size={20} /> : <Mic color={colors.text.inverse} size={21} />}</Pressable>
    </View>
  );
}
const styles = StyleSheet.create({
  bar: { flexDirection: 'row', alignItems: 'flex-end', gap: 10, paddingVertical: 12, borderTopWidth: 1, borderTopColor: colors.border.subtle, backgroundColor: 'rgba(11,16,32,0.94)' },
  input: { flex: 1, minHeight: 44, maxHeight: 120, borderRadius: 22, paddingHorizontal: 16, paddingVertical: 10, borderWidth: 1, borderColor: colors.border.subtle, backgroundColor: colors.surface.base, color: colors.text.primary, ...typography.bodyLg },
  button: { width: 44, height: 44, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.brand.cyan },
});
