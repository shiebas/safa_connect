#!/bin/bash

# Navigate to SAFA Global root
cd /home/shaun/safa_global

# Create mobile directory
mkdir -p mobile
cd mobile

# Install Expo CLI globally
echo "Installing Expo CLI..."
npm install -g @expo/cli

# Create Expo project
echo "Creating SafaCardApp with Expo..."
npx create-expo-app SafaCardApp --template blank

# Navigate to project
cd SafaCardApp

# Install navigation dependencies
echo "Installing navigation dependencies..."
npx expo install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npx expo install react-native-screens react-native-safe-area-context

# Install QR code dependencies
echo "Installing QR code dependencies..."
npx expo install expo-camera expo-barcode-scanner
npx expo install react-native-qrcode-svg
npx expo install @react-native-async-storage/async-storage

# Install other core dependencies
npx expo install expo-linear-gradient
npx expo install @expo/vector-icons
npx expo install axios
npx expo install expo-sharing

# Create basic app structure
echo "Setting up project structure..."
mkdir -p src/screens src/services src/components

# Create basic App.js for SAFA
cat > App.js << 'EOF'
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>SAFA Card App</Text>
      <Text style={styles.subtitle}>Digital Membership Cards</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFD700',
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  subtitle: {
    fontSize: 16,
    color: '#333',
    marginTop: 10,
  },
});
EOF

echo "✅ SafaCardApp (Expo) created successfully!"
echo "📁 Location: /home/shaun/safa_global/mobile/SafaCardApp"
echo ""
echo "🧹 Cleanup commands (run these):"
echo "rm -rf /home/shaun/safa_global/mobile/SafaCardApp"
echo "rm -rf /home/shaun/safa_global/mobile/node_modules"
echo ""
echo "📝 Next steps:"
echo "1. cd mobile/SafaCardApp"
echo "2. npx expo start"
echo "3. Install 'Expo Go' app on your phone"
echo "4. Scan QR code to test on device"
