#!/bin/bash

# Navigate to SAFA Global root
cd /home/shaun/safa_global

# Create mobile directory
mkdir -p mobile
cd mobile

# Check if React Native CLI is installed
if ! command -v npx @react-native-community/cli &> /dev/null; then
    echo "Installing React Native CLI..."
    npm install -g @react-native-community/cli
fi

# Create React Native project using the new CLI
echo "Creating SafaCardApp React Native project..."
npx @react-native-community/cli@latest init SafaCardApp

# Navigate to project
cd SafaCardApp

# Install core dependencies
echo "Installing core dependencies..."
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-qrcode-svg react-native-qrcode-scanner
npm install @react-native-async-storage/async-storage
npm install react-native-linear-gradient
npm install react-native-vector-icons
npm install axios

# Install additional dependencies for QR functionality
npm install react-native-camera react-native-permissions
npm install react-native-svg

# iOS specific (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Installing iOS dependencies..."
    cd ios && pod install && cd ..
fi

# Android specific permissions setup
echo "Setting up Android permissions..."
echo "Don't forget to add camera permissions to android/app/src/main/AndroidManifest.xml"

echo "✅ SafaCardApp created successfully!"
echo "📁 Location: /home/shaun/safa_global/mobile/SafaCardApp"
echo "📝 Next steps:"
echo "1. cd mobile/SafaCardApp"
echo "2. Add camera permissions to AndroidManifest.xml"
echo "3. npx react-native run-android"
