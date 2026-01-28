@echo off
REM Build script for React frontend (Windows)

echo Building React frontend...
cd frontend
call npm install
call npm run build
echo Build complete! Output in frontend/dist/
cd ..

