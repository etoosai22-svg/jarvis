import { CloudOff } from 'lucide-react-native';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, typography } from '@/theme/tokens';

/**
 * 경고 배너. 기본 제목은 "백엔드 미연결"이지만, 마이크 권한처럼 원인이 다르면
 * 제목을 넘겨야 한다 — 틀린 원인을 보여주면 사용자가 엉뚱한 곳을 고치게 된다.
 */
export function ConnectionNotice({
  message,
  title = '백엔드에 연결하지 못했습니다 — 예시 데이터를 표시합니다.',
}: {
  message: string;
  title?: string;
}) {
  return (
    <View style={styles.notice} accessibilityRole="alert">
      <CloudOff color="#FCD34D" size={18} />
      <View style={styles.body}>
        <Text style={styles.title}>{title}</Text>
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
