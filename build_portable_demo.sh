#!/bin/bash

# ================================================================
# safa_connect Portable Demo Builder
# Creates a self-contained demo for USB stick deployment
# ================================================================

set -e

echo "📦 Building safa_connect Portable Demo..."
echo "========================================"

DEMO_DIR="safa_connect_portable_demo"
BUILD_DIR="portable_build"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Clean and create build directory
print_status "Setting up build environment..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/$DEMO_DIR"

# Copy project files (excluding unnecessary files)
print_status "Copying project files..."
rsync -av --exclude='*.pyc' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='venv' \
          --exclude='node_modules' \
          --exclude='*.log' \
          --exclude='db.sqlite3' \
          --exclude='media/uploads' \
          --exclude='mobile' \
          --exclude='SafaCardApp' \
          --exclude='.env' \
          . "$BUILD_DIR/$DEMO_DIR/"

# Create portable Python environment structure
print_status "Creating portable Python structure..."
mkdir -p "$BUILD_DIR/$DEMO_DIR/portable_python"
mkdir -p "$BUILD_DIR/$DEMO_DIR/portable_libs"

# Create Windows batch launcher
print_status "Creating Windows launcher..."
cat > "$BUILD_DIR/$DEMO_DIR/LAUNCH_DEMO_WINDOWS.bat" << 'EOF'
@echo off
title safa_connect Demo Launcher
color 0A

echo =============================================
echo    safa_connect Demo - Portable Edition
echo =============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found on this system!
    echo.
    echo Please install Python 3.8+ from python.org
    echo Or use the Linux/Mac launcher if available.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found - setting up demo...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo [INFO] Installing requirements...
pip install -r requirements_production.txt

REM Setup demo environment
echo [INFO] Setting up demo database...
python manage.py migrate
python manage.py collectstatic --noinput

REM Create demo users
echo [INFO] Creating demo users...
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='demo_admin').exists():
    User.objects.create_superuser('demo_admin', 'admin@demo.com', 'SafaDemo2025!')
    print('Demo admin created')
if not User.objects.filter(username='demo_supporter').exists():
    User.objects.create_user('demo_supporter', 'supporter@demo.com', 'SafaDemo2025!')
    print('Demo supporter created')
"

REM Start server
echo [INFO] Starting safa_connect demo server...
echo.
echo =============================================
echo    Demo is ready! Opening browser...
echo =============================================
echo.
echo Web Interface: http://localhost:8000
echo Admin Panel:   http://localhost:8000/admin/
echo PWA Install:   http://localhost:8000/pwa/info/
echo.
echo Admin Login:   demo_admin / SafaDemo2025!
echo.
echo Press Ctrl+C to stop the demo
echo =============================================

REM Try to open browser
start http://localhost:8000

REM Start Django server
python manage.py runserver 8000

pause
EOF

# Create Linux/Mac launcher
print_status "Creating Linux/Mac launcher..."
cat > "$BUILD_DIR/$DEMO_DIR/launch_demo.sh" << 'EOF'
#!/bin/bash

# ================================================================
# safa_connect Portable Demo Launcher
# Cross-platform demo launcher for USB stick
# ================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}"
echo "============================================="
echo "   safa_connect Demo - Portable Edition"
echo "============================================="
echo -e "${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 not found!"
    echo "Please install Python 3.8+ and try again."
    echo ""
    echo "Installation links:"
    echo "- Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "- macOS: brew install python3"
    echo "- Or download from: https://python.org"
    exit 1
fi

echo -e "${BLUE}[INFO]${NC} Python found - setting up demo..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[INFO]${NC} Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}[INFO]${NC} Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo -e "${BLUE}[INFO]${NC} Installing requirements..."
pip install -r requirements_production.txt

# Setup database
echo -e "${BLUE}[INFO]${NC} Setting up demo database..."
python manage.py migrate
python manage.py collectstatic --noinput

# Create demo users
echo -e "${BLUE}[INFO]${NC} Creating demo users..."
python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='demo_admin').exists():
    User.objects.create_superuser('demo_admin', 'admin@demo.com', 'SafaDemo2025!')
    print('Demo admin created')
if not User.objects.filter(username='demo_supporter').exists():
    User.objects.create_user('demo_supporter', 'supporter@demo.com', 'SafaDemo2025!')
    print('Demo supporter created')
PYEOF

# Start server
echo ""
echo -e "${GREEN}============================================="
echo "   Demo is ready! Opening browser..."
echo "=============================================${NC}"
echo ""
echo "🌐 Web Interface: http://localhost:8000"
echo "🛠️  Admin Panel:   http://localhost:8000/admin/"
echo "📱 PWA Install:   http://localhost:8000/pwa/info/"
echo ""
echo "🔐 Admin Login:   demo_admin / SafaDemo2025!"
echo ""
echo "Press Ctrl+C to stop the demo"
echo -e "${GREEN}=============================================${NC}"
echo ""

# Try to open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000 &
elif command -v open &> /dev/null; then
    open http://localhost:8000 &
fi

# Start Django server
python manage.py runserver 8000
EOF

chmod +x "$BUILD_DIR/$DEMO_DIR/launch_demo.sh"

# Create portable README
print_status "Creating portable documentation..."
cat > "$BUILD_DIR/$DEMO_DIR/README_PORTABLE.md" << 'EOF'
# 🚀 safa_connect Portable Demo

## Quick Start

### Windows
Double-click: **`LAUNCH_DEMO_WINDOWS.bat`**

### Linux/Mac
Run: **`bash launch_demo.sh`**

## What You Need

- **Python 3.8+** installed on the target computer
- **Internet connection** for initial setup (downloads dependencies)
- **5-10 minutes** for first-time setup

## Demo Access

| Feature | URL | Login |
|---------|-----|-------|
| **Main Site** | http://localhost:8000 | - |
| **Admin Panel** | http://localhost:8000/admin/ | demo_admin / SafaDemo2025! |
| **Store** | http://localhost:8000/store/ | - |
| **PWA Install** | http://localhost:8000/pwa/info/ | - |

## Features Included

✅ **Complete safa_connect System**  
✅ **17+ Demo Products** in store  
✅ **Progressive Web App (PWA)**  
✅ **Offline Functionality**  
✅ **Multi-user Demo Accounts**  
✅ **Admin Management System**  
✅ **E-commerce Platform**  
✅ **Digital Membership Cards**  

## Demo Scenarios

1. **Homepage Tour** - Responsive design showcase
2. **User Registration** - Supporter and official signup
3. **Store Shopping** - Browse and purchase merchandise
4. **PWA Installation** - Install as desktop/mobile app
5. **Admin Management** - Backend administration features
6. **Offline Testing** - Disconnect internet and test functionality

## Troubleshooting

### Python Not Found
- **Windows**: Download from https://python.org
- **Ubuntu/Debian**: `sudo apt install python3 python3-pip`
- **macOS**: `brew install python3`

### Permission Denied (Linux/Mac)
```bash
chmod +x launch_demo.sh
bash launch_demo.sh
```

### Port Already in Use
The demo uses port 8000. If busy, stop other services or change port in launcher.

### Slow First Launch
First launch downloads dependencies (~100MB). Subsequent launches are faster.

## System Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for full installation
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8, 3.9, 3.10, 3.11, or 3.12

## Support

For technical support or customization:
- Check full documentation in project files
- Review DEMO_SETUP_GUIDE.md for detailed instructions
- Contact development team for enterprise deployment

---
**Professional Football Association Management - Anywhere, Anytime!** ⚽
EOF

# Create requirements specifically for portable demo
print_status "Creating portable requirements..."
cat > "$BUILD_DIR/$DEMO_DIR/requirements_portable.txt" << 'EOF'
# safa_connect Portable Demo Requirements
# Minimized for faster USB stick deployment

# Core Django
Django>=4.2.0,<5.0.0
djangorestframework>=3.14.0

# Database
dj-database-url>=3.0.0

# Authentication
django-allauth>=0.57.0
django-cors-headers>=4.3.1

# Forms & UI
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
django-widget-tweaks>=1.5.0

# File handling
Pillow>=10.0.1

# QR Codes
qrcode>=7.4.2

# Security
cryptography>=45.0.0

# Web Server
gunicorn>=21.2.0

# Utilities
requests>=2.32.3
python-decouple>=3.8
pytz>=2025.2
EOF

# Copy portable requirements as the main requirements for the portable version
cp "$BUILD_DIR/$DEMO_DIR/requirements_portable.txt" "$BUILD_DIR/$DEMO_DIR/requirements_production.txt"

# Create demo environment file
print_status "Creating portable environment configuration..."
cat > "$BUILD_DIR/$DEMO_DIR/.env.portable" << 'EOF'
# safa_connect Portable Demo Environment
DEBUG=True
SECRET_KEY=portable-demo-key-not-for-production
DATABASE_URL=sqlite:///portable_demo.db
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Demo settings
DEMO_MODE=True
USE_DEMO_DATA=True

# Email (console for demo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Static files
STATIC_ROOT=staticfiles_portable/
MEDIA_ROOT=media_portable/
EOF

# Create autorun file for Windows (optional)
print_status "Creating Windows autorun..."
cat > "$BUILD_DIR/$DEMO_DIR/autorun.inf" << 'EOF'
[autorun]
label=safa_connect Demo
icon=static\images\safa_logo_small.png
open=LAUNCH_DEMO_WINDOWS.bat
action=Launch safa_connect Demo
EOF

# Create portable info file
print_status "Creating demo information..."
cat > "$BUILD_DIR/$DEMO_DIR/DEMO_INFO.txt" << 'EOF'
===============================================
    safa_connect Portable Demo
    South African Football Association
    Management System Demonstration
===============================================

VERSION: Portable USB Edition
DATE: June 2025
SIZE: ~500MB when fully installed

WHAT'S INCLUDED:
- Complete safa_connect management system
- 17+ demo products in merchandise store
- Progressive Web App (PWA) functionality
- Multi-user demo accounts
- Offline capabilities
- Admin management tools

QUICK START:
1. Windows: Double-click LAUNCH_DEMO_WINDOWS.bat
2. Linux/Mac: Run "bash launch_demo.sh"
3. Open http://localhost:8000 in browser
4. Login with demo_admin / SafaDemo2025!

REQUIREMENTS:
- Python 3.8+ installed
- Internet connection for initial setup
- 5-10 minutes for first launch

For full documentation, see README_PORTABLE.md

===============================================
Professional Football Management - Portable!
===============================================
EOF

# Create ZIP package
print_status "Creating portable package..."
cd "$BUILD_DIR"
zip -r "safa_connect_portable_demo.zip" "$DEMO_DIR/"
cd ..

print_success "Portable demo package created!"

echo ""
echo "📦 PORTABLE DEMO PACKAGE READY!"
echo "================================="
echo ""
echo "📁 Package Location: $BUILD_DIR/safa_connect_portable_demo.zip"
echo "📊 Package Contents:"
echo "   ✅ Complete safa_connect system"
echo "   ✅ Windows launcher (.bat file)"
echo "   ✅ Linux/Mac launcher (.sh file)"
echo "   ✅ Portable documentation"
echo "   ✅ Demo data and users"
echo "   ✅ Autorun configuration"
echo ""
echo "🚀 USB Stick Instructions:"
echo "   1. Copy safa_connect_portable_demo.zip to USB stick"
echo "   2. Extract on target computer"
echo "   3. Run appropriate launcher for OS"
echo "   4. Demo starts automatically!"
echo ""
echo "💾 Compatible With:"
echo "   ✅ Windows 10/11"
echo "   ✅ macOS 10.14+"
echo "   ✅ Ubuntu 18.04+"
echo "   ✅ Any system with Python 3.8+"
echo ""
echo "🎯 Perfect for presentations, sales demos, and training!"

print_success "Portable demo build complete!"
