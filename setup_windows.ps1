# SAFA Django Project Windows Setup Script
Write-Host "Setting up SAFA Django Project on Windows..." -ForegroundColor Green
Write-Host ""

# Step 1: Check Python installation
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "Python not found. Please install Python 3.11+ from python.org" -ForegroundColor Red
    Write-Host "Or run: winget install Python.Python.3.11" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Remove old Linux virtual environment
Write-Host "Step 2: Removing old Linux virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv"
    Write-Host "Old virtual environment removed." -ForegroundColor Green
}

# Step 3: Create new Windows virtual environment
Write-Host "Step 3: Creating new Windows virtual environment..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Failed to create virtual environment." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 4: Activate virtual environment and install requirements
Write-Host "Step 4: Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host "Step 5: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "Step 6: Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "Step 7: Running Django migrations..." -ForegroundColor Yellow
python manage.py migrate

Write-Host "Step 8: Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

Write-Host ""
Write-Host "Setup complete! You can now run the server with:" -ForegroundColor Green
Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "python manage.py runserver" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to continue"
