export const colors = {
  bg: { app: '#070A12', depth: '#0B1020' },
  surface: { base: '#111827', raised: '#182235', glass: 'rgba(17, 24, 39, 0.72)' },
  border: { subtle: '#243047', focus: '#7DD3FC' },
  text: { primary: '#F8FAFC', secondary: '#CBD5E1', tertiary: '#94A3B8', disabled: '#64748B', inverse: '#020617' },
  brand: { cyan: '#38BDF8', cyanDeep: '#0284C7', cyanSoft: '#0C4A6E', violet: '#8B5CF6', violetSoft: '#2E1F59' },
  semantic: { success: '#22C55E', successBg: '#052E16', warning: '#F59E0B', warningBg: '#451A03', error: '#F87171', errorBg: '#450A0A', info: '#60A5FA' },
} as const;

export const typography = {
  hero: { fontSize: 32, lineHeight: 40, fontWeight: '800' as const, letterSpacing: -0.64 },
  titleLg: { fontSize: 24, lineHeight: 32, fontWeight: '700' as const, letterSpacing: -0.24 },
  titleMd: { fontSize: 20, lineHeight: 28, fontWeight: '700' as const, letterSpacing: -0.2 },
  titleSm: { fontSize: 17, lineHeight: 24, fontWeight: '700' as const },
  bodyLg: { fontSize: 16, lineHeight: 24, fontWeight: '400' as const },
  bodyMd: { fontSize: 14, lineHeight: 22, fontWeight: '400' as const },
  labelMd: { fontSize: 13, lineHeight: 18, fontWeight: '600' as const, letterSpacing: 0.13 },
  caption: { fontSize: 12, lineHeight: 16, fontWeight: '500' as const, letterSpacing: 0.24 },
  button: { fontSize: 16, lineHeight: 22, fontWeight: '700' as const },
} as const;

export const spacing = { 2: 2, 4: 4, 6: 6, 8: 8, 10: 10, 12: 12, 16: 16, 20: 20, 24: 24, 32: 32, 40: 40, 48: 48, 64: 64, 80: 80 } as const;
export const radius = { xs: 6, sm: 10, md: 14, lg: 18, xl: 24, xxl: 32, pill: 999 } as const;
export const size = { touchMin: 44, header: 56, bottomTab: 72, input: 52, button: 52, buttonSm: 44, orb: 164, orbCompact: 104, icon: 22, iconTab: 24 } as const;
export const shadow = {
  card: { shadowColor: '#000000', shadowOpacity: 0.22, shadowRadius: 18, shadowOffset: { width: 0, height: 10 }, elevation: 8 },
  orb: { shadowColor: '#38BDF8', shadowOpacity: 0.36, shadowRadius: 32, shadowOffset: { width: 0, height: 0 }, elevation: 12 },
} as const;
