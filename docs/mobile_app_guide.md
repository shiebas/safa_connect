# SAFA Mobile App Setup & Usage Guide

This guide provides instructions for setting up and using the SAFA Mobile Application for digital membership cards.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running the App](#running-the-app)
4. [App Features](#app-features)
5. [Integration with Digital Card System](#integration-with-digital-card-system)
6. [Troubleshooting](#troubleshooting)
7. [Development Notes](#development-notes)

## Prerequisites

Before you begin, make sure you have the following installed:

- Node.js (v18 or higher)
- npm (v9 or higher)
- Expo CLI (`npm install -g expo-cli`)
- For iOS testing: Xcode (Mac only)
- For Android testing: Android Studio

You'll also need:
- A physical device with Expo Go app installed OR
- iOS Simulator (Mac only) OR
- Android Emulator

## Installation

1. Navigate to the project directory:

```bash
cd /home/shaun/safa_global
```

2. Run the setup script to install the necessary dependencies:

```bash
./setup_mobile_expo.sh
```

3. Alternatively, you can manually install the dependencies:

```bash
cd mobile/SafaCardApp
npm install
```

## Running the App

### Using Expo Go (Recommended for Development)

1. Start the development server:

```bash
cd mobile/SafaCardApp
npx expo start
```

2. This will display a QR code in the terminal

3. On your device:
   - **iOS**: Scan the QR code with the Camera app
   - **Android**: Scan the QR code with the Expo Go app

### Using Emulator/Simulator

From the Expo development server:

- Press `i` to open in iOS Simulator (Mac only)
- Press `a` to open in Android Emulator

### Building Standalone Apps

To create standalone apps for app stores:

```bash
cd mobile/SafaCardApp
eas build --platform ios
eas build --platform android
```

You'll need to configure the `eas.json` file and have an Expo account for this to work.

## App Features

The SAFA Mobile App includes the following key features:

1. **User Authentication**
   - Login using SAFA credentials
   - Token-based authentication with auto-renewal

2. **Digital Membership Card**
   - Digital representation of SAFA membership card
   - Front and back card views with flip animation
   - QR code display for verification
   - Card details including status, expiry date, etc.

3. **Google Wallet Integration**
   - Add membership card to Google Wallet (Android)
   - Planned: Apple Wallet integration (iOS)

4. **User Profile**
   - View and manage profile information
   - Check membership status and history
   - View associated clubs and roles

5. **Offline Mode**
   - Access digital card when offline
   - Cached profile information

## Integration with Digital Card System

The mobile app connects to the SAFA backend using REST API endpoints:

### Key Endpoints

| Endpoint | Purpose |
|---------|---------|
| `/accounts/api/token/` | Authentication |
| `/accounts/api/profile/` | User profile data |
| `/membership-cards/api/digitalcards/my-card/` | Digital card data |
| `/membership-cards/qr-code/` | QR code data |

### Data Flow

1. User logs in and receives an authentication token
2. App fetches user profile and card information
3. Card data is cached locally for offline access
4. QR code updates are synchronized when online

## Troubleshooting

### Common Issues

**App fails to connect to backend:**
- Verify the server is running
- Check API URLs in `src/services/api.js`
- Ensure network connectivity

**Login fails:**
- Verify credentials
- Check server logs for authentication issues
- Confirm user has active membership

**QR code doesn't display:**
- Refresh card data
- Check if QR data is being properly fetched
- Verify QR code generation on server side

**App crashes on startup:**
- Clear app cache and data
- Reinstall the Expo Go app
- Update to latest Expo SDK

## Development Notes

### Project Structure

```
SafaCardApp/
├── App.js                  # Main application entry point
├── app.json                # Expo configuration
├── src/
│   ├── AppNavigator.js     # Navigation configuration
│   ├── screens/
│   │   ├── LoginScreen.js  # Authentication screen
│   │   ├── DigitalCardScreen.js  # Digital card display
│   │   └── ProfileScreen.js      # User profile screen
│   ├── components/         # Reusable UI components
│   └── services/
│       └── api.js          # API service for backend communication
├── assets/                 # Images and other static assets
└── package.json            # Dependencies and scripts
```

### Key Libraries Used

- **@react-navigation**: Screen navigation
- **expo-linear-gradient**: Gradient backgrounds
- **react-native-qrcode-svg**: QR code display
- **@react-native-async-storage/async-storage**: Local data persistence
- **axios**: API communication

### Backend Integration

The app is designed to work with the Django backend providing the digital card API. Make sure the backend is properly configured with the following:

1. Authentication endpoints with token support
2. Digital card endpoints that provide card details
3. QR code generation endpoints
4. CORS headers for mobile app access

### Customizing the App

To customize the app for different environments:

1. Update the `BASE_URL` in `src/services/api.js`
2. Replace SAFA logos in the `assets` folder
3. Adjust colors in the theme (primarily in `styles` objects)

---

For additional support, contact the SAFA development team at dev-support@safa.org.za.

*Last updated: June 17, 2025*
