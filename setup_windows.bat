@echo off
echo Setting up SAFA Django Project on Windows...
echo.

echo Step 1: Refreshing environment variables...
call refreshenv

echo Step 2: Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.11+ from python.org
    echo Or run: winget install Python.Python.3.11
    pause
    exit /b 1
)

echo Step 3: Removing old Linux virtual environment...
if exist venv (
    rmdir /s /q venv
    echo Old virtual environment removed.
)

echo Step 4: Creating new Windows virtual environment...
python -m venv venv

echo Step 5: Activating virtual environment...
call venv\Scripts\activate.bat

echo Step 6: Upgrading pip...
python -m pip install --upgrade pip

echo Step 7: Installing requirements...
pip install -r requirements.txt

echo Step 8: Running Django migrations...
python manage.py migrate

echo Step 9: Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Setup complete! You can now run the server with:
echo venv\Scripts\activate.bat
echo python manage.py runserver
echo.
pause
