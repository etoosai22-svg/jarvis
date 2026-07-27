import { CalendarDays, Cloud, Mail, NotebookTabs } from 'lucide-react-native';
import { Text } from 'react-native';
import { Row, StatusPill } from '@/components/common';
import { colors } from '@/theme/tokens';
import type { Integration } from '@/types/models';

const map = {
  connected: { label: '연결됨', tone: 'success' as const }, expired: { label: '재인증', tone: 'warning' as const }, disconnected: { label: '연결 안 됨', tone: 'muted' as const }, error: { label: '오류', tone: 'error' as const },
};

export function IntegrationRow({ integration }: { integration: Integration }) {
  const Icon = integration.id === 'calendar' ? CalendarDays : integration.id === 'gmail' ? Mail : integration.id === 'notion' ? NotebookTabs : Cloud;
  const status = map[integration.status];
  return <Row icon={<Icon color={colors.brand.cyan} size={20} />} title={integration.title} subtitle={integration.subtitle} right={<><StatusPill label={status.label} tone={status.tone} /><Text style={{ color: colors.text.tertiary, marginLeft: 8 }}>›</Text></>} />;
}
