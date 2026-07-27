import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Brain, CheckSquare, Home, MessageCircle, Settings } from 'lucide-react-native';
import { colors, size } from '@/theme/tokens';
import { ConversationScreen } from '@/screens/ConversationScreen';
import { HomeScreen } from '@/screens/HomeScreen';
import { MemoryScreen } from '@/screens/MemoryScreen';
import { SettingsScreen } from '@/screens/SettingsScreen';
import { TasksScreen } from '@/screens/TasksScreen';

export type RootTabParamList = {
  Home: undefined;
  Conversation: undefined;
  Tasks: undefined;
  Memory: undefined;
  Settings: undefined;
};

const Tab = createBottomTabNavigator<RootTabParamList>();
const iconMap = { Home, Conversation: MessageCircle, Tasks: CheckSquare, Memory: Brain, Settings };
const labelMap = { Home: 'Home', Conversation: 'Talk', Tasks: 'Tasks', Memory: 'Memory', Settings: 'Settings' };

export function AppNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.brand.cyan,
        tabBarInactiveTintColor: colors.text.tertiary,
        tabBarStyle: { height: size.bottomTab, paddingTop: 8, paddingBottom: 10, backgroundColor: 'rgba(11,16,32,0.96)', borderTopColor: colors.border.subtle },
        tabBarLabelStyle: { fontSize: 11, fontWeight: '700' },
        tabBarIcon: ({ color, size: iconSize }) => {
          const Icon = iconMap[route.name];
          return <Icon color={color} size={iconSize} strokeWidth={2.2} />;
        },
        tabBarAccessibilityLabel: `${labelMap[route.name]} 탭`,
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ tabBarLabel: 'Home' }} />
      <Tab.Screen name="Conversation" component={ConversationScreen} options={{ tabBarLabel: 'Talk' }} />
      <Tab.Screen name="Tasks" component={TasksScreen} options={{ tabBarLabel: 'Tasks' }} />
      <Tab.Screen name="Memory" component={MemoryScreen} options={{ tabBarLabel: 'Memory' }} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{ tabBarLabel: 'Settings' }} />
    </Tab.Navigator>
  );
}
