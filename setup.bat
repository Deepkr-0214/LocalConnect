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
echo 🗄️ Checking database...
if not exist "instance" mkdir instance

echo.
echo ✅ Setup complete! 
echo.
echo 🚀 You can now run the application with:
echo    start_server.bat
echo.
echo    OR manually with:
echo    python app.py
echo.

pause