@echo off
echo.
echo ================================================
echo    🚀 Starting LocalConnect Application
echo ================================================
echo.
echo 📍 Server will be available at:
echo    http://127.0.0.1:5000
echo.
echo 🏪 Example vendor page:
echo    http://127.0.0.1:5000/customer/vendor/7
echo.
echo ⚡ Press Ctrl+C to stop the server
echo.
echo ================================================
echo.

cd /d "%~dp0"
python app.py

pause