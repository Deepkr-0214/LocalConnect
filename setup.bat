@echo off
echo.
echo ================================================
echo    🔧 LocalConnect Setup & Dependency Check
echo ================================================
echo.

cd /d "%~dp0"

echo 📦 Installing Python dependencies...
python -m pip install -r requirements.txt

echo.
echo 🗄️ Checking database and migrations...
if not exist "instance" mkdir instance
python manage.py migrate

echo.
echo ✅ Setup complete! 
echo.
echo 🚀 You can now run the application with:
echo    start_server.bat
echo.
echo    OR manually with:
echo    python manage.py runserver 0.0.0.0:8000
echo.

pause