#!/bin/bash
# Script to start Expo in the correct directory for the mobile app
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/mobile/SafaCardApp" || exit 1
npx expo start -c
