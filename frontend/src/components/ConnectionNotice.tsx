import { CloudOff } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, typography } from '@/theme/tokens';

/** 백엔드 연결이 끊겨 목업 데이터를 보여주고 있음을 알린다. */
export function ConnectionNotice({ message }: { message: string }) {
  return (
    <View style={styles.notice} accessibilityRole="alert">
      <CloudOff color="#FCD34D" size={18} />
      <View style={styles.body}>
        <Text style={styles.title}>백엔드에 연결하지 못했습니다 — 예시 데이터를 표시합니다.</Text>
        <Text style={styles.sub} numberOfLines={2}>{message}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  notice: { flexDirection: 'row', gap: 10, alignItems: 'flex-start', padding: 12, marginBottom: 12, borderRadius: radius.lg, backgroundColor: colors.semantic.warningBg, borderWidth: 1, borderColor: 'rgba(245,158,11,0.32)' },
  body: { flex: 1, minWidth: 0 },
  title: { ...typography.labelMd, color: '#FCD34D', fontWeight: '800' },
  sub: { ...typography.caption, color: colors.text.tertiary, marginTop: 2 },
});
