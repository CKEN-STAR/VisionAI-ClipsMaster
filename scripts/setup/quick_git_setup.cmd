@echo off
echo VisionAI-ClipsMaster Git Setup
echo ================================

cd /d "D:\zancun\VisionAI-ClipsMaster"

echo Step 1: Check Git installation
git --version
if errorlevel 1 (
    echo ERROR: Git not found. Please install Git first.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Step 2: Initialize Git repository
git init
git branch -M main

echo Step 3: Configure user information
git config user.name "CKEN"
git config user.email "your-email@example.com"

echo Step 4: Add remote repository
git remote remove origin 2>nul
git remote add origin https://github.com/CKEN/VisionAI-ClipsMaster.git

echo Step 5: Create .gitignore file
(
echo # VisionAI-ClipsMaster .gitignore
echo.
echo # Python
echo __pycache__/
echo *.py[cod]
echo *.so
echo .Python
echo build/
echo dist/
echo *.egg-info/
echo.
echo # Virtual Environment
echo venv/
echo env/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
echo.
echo # Logs
echo *.log
echo logs/
echo.
echo # Models
echo models/*.gguf
echo models/*.bin
echo models/*.safetensors
echo.
echo # Temporary files
echo temp/
echo tmp/
echo cache/
echo.
echo # User data
echo user_data/
echo uploads/
echo downloads/
echo.
echo # Config files
echo config/secrets.json
echo .env
echo.
echo # Test files
echo test_videos/
echo test_outputs/
) > .gitignore

echo Step 6: Add files to staging
git add .

echo Step 7: Create initial commit
git commit -m "Initial commit: VisionAI-ClipsMaster v1.0.0"

echo Step 8: Push to GitHub
echo WARNING: This may require GitHub authentication
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed. This may be due to:
    echo 1. Authentication required
    echo 2. Repository doesn't exist on GitHub
    echo 3. Network connectivity issues
    echo.
    echo Please try:
    echo 1. Use GitHub Desktop for easier authentication
    echo 2. Create Personal Access Token
    echo 3. Check if repository exists on GitHub
)

echo.
echo Setup complete!
pause
