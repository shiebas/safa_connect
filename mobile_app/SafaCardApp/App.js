import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import CardScreen from './src/screens/CardScreen';
import ScannerScreen from './src/screens/ScannerScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import SplashScreen from './src/screens/SplashScreen';

// Services
import { AuthService } from './src/services/AuthService';
import { StorageService } from './src/services/StorageService';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// SAFA Brand Colors
const COLORS = {
  primary: '#FFD700',    // SAFA Gold
  secondary: '#000000',  // Black
  background: '#FFFFFF', // White
  text: '#000000'
};

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          
          if (route.name === 'MyCard') {
            iconName = 'credit-card';
          } else if (route.name === 'Scanner') {
            iconName = 'qr-code-scanner';
          } else if (route.name === 'Profile') {
            iconName = 'person';
          }
          
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: 'gray',
        tabBarStyle: {
          backgroundColor: COLORS.background,
          borderTopColor: COLORS.primary,
          borderTopWidth: 2
        },
        headerStyle: {
          backgroundColor: COLORS.primary,
        },
        headerTintColor: COLORS.secondary,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen 
        name="MyCard" 
        component={CardScreen} 
        options={{ title: 'My SAFA Card' }}
      />
      <Tab.Screen 
        name="Scanner" 
        component={ScannerScreen} 
        options={{ title: 'QR Scanner' }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen} 
        options={{ title: 'Profile' }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await StorageService.getToken();
      const isValid = await AuthService.validateToken(token);
      setIsAuthenticated(isValid);
    } catch (error) {
      console.log('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated ? (
          <Stack.Screen name="MainTabs" component={MainTabs} />
        ) : (
          <Stack.Screen name="Login" component={LoginScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
