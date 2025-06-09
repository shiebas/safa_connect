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

echo "✅ SafaCardApp (Expo) created successfully!"
echo "📁 Location: /home/shaun/safa_global/mobile/SafaCardApp"
echo "📝 Next steps:"
echo "1. cd mobile/SafaCardApp"
echo "2. npx expo start"
echo "3. Scan QR code with Expo Go app on your phone"
