#!/bin/bash

# ================================================================
# SAFA Connect Demo Setup Script
# Automated setup for demonstration environment
# ================================================================

set -e  # Exit on any error

echo "🚀 SAFA Connect Demo Setup Starting..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Python 3 is installed
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1,2)
print_success "Python $PYTHON_VERSION found"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "manage.py not found. Please run this script from the SAFA Connect project root."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing requirements..."
if [ -f "requirements_production.txt" ]; then
    pip install -r requirements_production.txt
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_error "No requirements file found!"
    exit 1
fi
print_success "Requirements installed successfully"

# Setup environment variables for demo
print_status "Setting up demo environment..."
cat > .env << EOF
# SAFA Connect Demo Environment
DEBUG=True
SECRET_KEY=demo-secret-key-for-development-only-not-for-production
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Demo settings
DEMO_MODE=True
USE_DEMO_DATA=True

# Email settings (console backend for demo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Static files
STATIC_ROOT=staticfiles/
MEDIA_ROOT=media/

# Google Wallet (demo keys - replace with real keys for production)
GOOGLE_WALLET_ISSUER_ID=demo_issuer_id
GOOGLE_WALLET_SERVICE_ACCOUNT_EMAIL=demo@example.com
EOF
print_success "Environment variables configured"

# Run migrations
print_status "Running database migrations..."
python manage.py makemigrations
python manage.py migrate
print_success "Database migrations completed"

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput
print_success "Static files collected"

# Create superuser for demo
print_status "Creating demo superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Create demo admin user
if not User.objects.filter(username='demo_admin').exists():
    User.objects.create_superuser(
        username='demo_admin',
        email='admin@safademo.com',
        password='SafaDemo2025!',
        first_name='Demo',
        last_name='Administrator'
    )
    print("Demo admin user created")
else:
    print("Demo admin user already exists")

# Create demo supporter
if not User.objects.filter(username='demo_supporter').exists():
    User.objects.create_user(
        username='demo_supporter',
        email='supporter@safademo.com',
        password='SafaDemo2025!',
        first_name='Demo',
        last_name='Supporter'
    )
    print("Demo supporter user created")
else:
    print("Demo supporter user already exists")

# Create demo referee
if not User.objects.filter(username='demo_referee').exists():
    User.objects.create_user(
        username='demo_referee',
        email='referee@safademo.com',
        password='SafaDemo2025!',
        first_name='Demo',
        last_name='Referee'
    )
    print("Demo referee user created")
else:
    print("Demo referee user already exists")
EOF
print_success "Demo users created"

# Load demo data if fixtures exist
print_status "Loading demo data..."
if [ -d "fixtures" ]; then
    for fixture in fixtures/*.json; do
        if [ -f "$fixture" ]; then
            print_status "Loading $(basename $fixture)..."
            python manage.py loaddata "$fixture" || print_warning "Could not load $fixture"
        fi
    done
fi
print_success "Demo data loading completed"

# Create demo content
print_status "Creating demo merchandise..."
python manage.py shell << EOF
from merchandise.models import Category, Product
from decimal import Decimal

# Create categories
categories = [
    {'name': 'Jerseys & Team Wear', 'description': 'Official SAFA jerseys and team uniforms'},
    {'name': 'Training Equipment', 'description': 'Professional training gear and equipment'},
    {'name': 'Accessories', 'description': 'SAFA branded accessories and merchandise'},
    {'name': 'Keychains', 'description': 'Collectible keychains and small items'},
    {'name': 'Supporter Gear', 'description': 'Fan merchandise and supporter items'},
    {'name': 'Official Documents', 'description': 'Certificates and official documentation'},
]

for cat_data in categories:
    category, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'description': cat_data['description']}
    )
    if created:
        print(f"Created category: {category.name}")

# Create demo products
products = [
    {
        'name': 'SAFA Home Jersey 2025',
        'description': 'Official South African national team home jersey',
        'price': Decimal('899.99'),
        'category': 'Jerseys & Team Wear',
        'is_featured': True,
        'is_new': True,
    },
    {
        'name': 'SAFA Away Jersey 2025',
        'description': 'Official South African national team away jersey',
        'price': Decimal('899.99'),
        'category': 'Jerseys & Team Wear',
        'is_featured': True,
    },
    {
        'name': 'Training Football',
        'description': 'Professional training football',
        'price': Decimal('299.99'),
        'category': 'Training Equipment',
        'discount_percentage': 15,
    },
    {
        'name': 'SAFA Scarf',
        'description': 'Official supporter scarf in SAFA colors',
        'price': Decimal('149.99'),
        'category': 'Supporter Gear',
        'is_new': True,
    },
    {
        'name': 'SAFA Keychain',
        'description': 'Metal keychain with SAFA logo',
        'price': Decimal('49.99'),
        'category': 'Keychains',
        'discount_percentage': 20,
    },
]

for prod_data in products:
    category = Category.objects.get(name=prod_data['category'])
    product, created = Product.objects.get_or_create(
        name=prod_data['name'],
        defaults={
            'description': prod_data['description'],
            'price': prod_data['price'],
            'category': category,
            'is_featured': prod_data.get('is_featured', False),
            'is_new': prod_data.get('is_new', False),
            'discount_percentage': prod_data.get('discount_percentage', 0),
            'stock_quantity': 100,
        }
    )
    if created:
        print(f"Created product: {product.name}")

print("Demo merchandise created successfully!")
EOF

print_success "Demo merchandise created"

# Start the development server in background
print_status "Starting Django development server..."

# Kill any existing Django processes
pkill -f "python.*manage.py.*runserver" || true

# Start server in background
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    print_success "Django server started successfully (PID: $SERVER_PID)"
else
    print_error "Failed to start Django server"
    exit 1
fi

# Display demo information
echo ""
echo "🎉 SAFA Connect Demo Setup Complete!"
echo "======================================"
echo ""
echo "📍 Demo Access Points:"
echo "   🌐 Main Website:     http://localhost:8000"
echo "   🛠️  Admin Panel:      http://localhost:8000/admin/"
echo "   🛒 Store Demo:       http://localhost:8000/store/"
echo "   📱 PWA Installation: http://localhost:8000/pwa/info/"
echo ""
echo "🔐 Demo Login Credentials:"
echo "   👤 Admin:     demo_admin / SafaDemo2025!"
echo "   ⚽ Referee:   demo_referee / SafaDemo2025!"
echo "   💚 Supporter: demo_supporter / SafaDemo2025!"
echo ""
echo "📊 Demo Features Available:"
echo "   ✅ User Registration (Supporters & Officials)"
echo "   ✅ E-Commerce Store (17+ Products)"
echo "   ✅ Progressive Web App (PWA)"
echo "   ✅ Multi-level Admin System"
echo "   ✅ Offline Functionality"
echo "   ✅ Digital Membership Cards"
echo "   ✅ Document Protection & Watermarking"
echo ""
echo "🚀 Quick Demo Scenarios:"
echo "   1. Visit main site and install PWA"
echo "   2. Register as supporter at /supporters/register/"
echo "   3. Browse store and add items to cart"
echo "   4. Login as admin and explore admin panel"
echo "   5. Test offline functionality"
echo ""
echo "🛑 To Stop Demo:"
echo "   kill $SERVER_PID"
echo "   # or run: bash stop_demo.sh"
echo ""
echo "📚 Full Documentation: DEMO_SETUP_GUIDE.md"
echo ""

# Create stop script
cat > stop_demo.sh << EOF
#!/bin/bash
echo "Stopping SAFA Connect demo..."
pkill -f "python.*manage.py.*runserver" || true
echo "Demo stopped."
EOF
chmod +x stop_demo.sh

# Save server PID for later reference
echo $SERVER_PID > .demo_server.pid

print_success "Demo is ready! Open http://localhost:8000 in your browser."

# Optional: Open browser automatically (uncomment if desired)
# if command -v xdg-open &> /dev/null; then
#     xdg-open http://localhost:8000
# elif command -v open &> /dev/null; then
#     open http://localhost:8000
# fi

echo ""
echo "🎯 Happy Demoing! ⚽"
