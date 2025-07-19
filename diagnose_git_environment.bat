@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ================================================================================
echo VisionAI-ClipsMaster Git Environment Diagnostic Tool
echo ================================================================================
echo.

set "PROJECT_DIR=%~dp0"
set "GITHUB_URL=https://github.com/CKEN/VisionAI-ClipsMaster.git"

echo Diagnostic Time: %date% %time%
echo Project Directory: %PROJECT_DIR%
echo Target Repository: %GITHUB_URL%
echo.

echo ================================================================================
echo [1/7] System Environment Check
echo ================================================================================

echo Operating System: %OS%
echo Computer Name: %COMPUTERNAME%
echo User Name: %USERNAME%
echo Current Directory: %CD%
echo.

echo ================================================================================
echo [2/7] Git Installation Check
echo ================================================================================

echo Checking Git installation...
git --version 2>nul
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo.
    echo Solutions:
    echo 1. Download Git from: https://git-scm.com/download/win
    echo 2. Make sure Git is added to system PATH
    echo 3. Restart command prompt after installation
    echo.
    set "GIT_AVAILABLE=false"
) else (
    echo SUCCESS: Git is available
    set "GIT_AVAILABLE=true"
)

echo.
echo Checking Git configuration...
if "!GIT_AVAILABLE!"=="true" (
    echo Git user.name: 
    git config user.name 2>nul || echo [Not configured]
    echo Git user.email: 
    git config user.email 2>nul || echo [Not configured]
) else (
    echo SKIPPED: Git not available
)

echo.
echo ================================================================================
echo [3/7] Git LFS Check
echo ================================================================================

echo Checking Git LFS installation...
git lfs version 2>nul
if errorlevel 1 (
    echo WARNING: Git LFS is not installed
    echo Download from: https://git-lfs.github.io/
    echo Note: Git LFS is optional but recommended for large files
    set "LFS_AVAILABLE=false"
) else (
    echo SUCCESS: Git LFS is available
    set "LFS_AVAILABLE=true"
)

echo.
echo ================================================================================
echo [4/7] Directory and Permissions Check
echo ================================================================================

echo Checking project directory access...
cd /d "%PROJECT_DIR%" 2>nul
if errorlevel 1 (
    echo ERROR: Cannot access project directory: %PROJECT_DIR%
    echo Check if the directory exists and you have permissions
) else (
    echo SUCCESS: Project directory accessible
)

echo.
echo Checking write permissions...
echo test > test_write_permission.tmp 2>nul
if exist test_write_permission.tmp (
    echo SUCCESS: Write permissions available
    del test_write_permission.tmp >nul 2>&1
) else (
    echo ERROR: No write permissions in current directory
    echo Try running as administrator or check folder permissions
)

echo.
echo ================================================================================
echo [5/7] Network Connectivity Check
echo ================================================================================

echo Checking internet connectivity...
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo WARNING: No internet connectivity detected
    echo This may affect GitHub operations
) else (
    echo SUCCESS: Internet connectivity available
)

echo.
echo Checking GitHub connectivity...
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo WARNING: Cannot reach github.com
    echo Check firewall settings or network restrictions
) else (
    echo SUCCESS: GitHub is reachable
)

echo.
echo ================================================================================
echo [6/7] Existing Git Repository Check
echo ================================================================================

if exist ".git" (
    echo INFO: Existing Git repository found
    echo.
    if "!GIT_AVAILABLE!"=="true" (
        echo Current branch:
        git branch --show-current 2>nul || echo [Cannot determine]
        echo.
        echo Remote repositories:
        git remote -v 2>nul || echo [No remotes configured]
        echo.
        echo Repository status:
        git status --porcelain 2>nul || echo [Cannot get status]
    )
) else (
    echo INFO: No existing Git repository found
    echo This is normal for a new project setup
)

echo.
echo ================================================================================
echo [7/7] File System Check
echo ================================================================================

echo Checking important files...
if exist "README.md" (
    echo SUCCESS: README.md found
) else (
    echo WARNING: README.md not found
)

if exist "requirements.txt" (
    echo SUCCESS: requirements.txt found
) else (
    echo WARNING: requirements.txt not found
)

if exist "VisionAI-ClipsMaster-Core\simple_ui_fixed.py" (
    echo SUCCESS: Main application file found
) else (
    echo WARNING: Main application file not found
)

echo.
echo Checking for potential issues...
if exist ".git\index.lock" (
    echo WARNING: Git index lock file found
    echo This may indicate a previous Git operation was interrupted
    echo Solution: Delete .git\index.lock file
)

echo.
echo ================================================================================
echo Diagnostic Summary
echo ================================================================================

echo.
echo Environment Status:
if "!GIT_AVAILABLE!"=="true" (
    echo [OK] Git is installed and available
) else (
    echo [ERROR] Git is not available - MUST FIX
)

if "!LFS_AVAILABLE!"=="true" (
    echo [OK] Git LFS is available
) else (
    echo [WARN] Git LFS not available - recommended to install
)

echo.
echo Recommendations:
if "!GIT_AVAILABLE!"=="false" (
    echo 1. CRITICAL: Install Git from https://git-scm.com/download/win
    echo 2. Add Git to system PATH during installation
    echo 3. Restart command prompt after installation
)

if "!LFS_AVAILABLE!"=="false" (
    echo 4. OPTIONAL: Install Git LFS from https://git-lfs.github.io/
)

echo 5. Ensure you have GitHub account and repository created
echo 6. Consider using GitHub Desktop for easier authentication

echo.
echo ================================================================================
echo Manual Setup Commands (if script fails)
echo ================================================================================

echo.
echo If the automated script fails, use these manual commands:
echo.
echo # 1. Initialize repository
echo git init
echo git branch -M main
echo.
echo # 2. Configure user
echo git config user.name "CKEN"
echo git config user.email "your-email@example.com"
echo.
echo # 3. Add remote
echo git remote add origin %GITHUB_URL%
echo.
echo # 4. Add and commit files
echo git add .
echo git commit -m "Initial commit"
echo.
echo # 5. Push to GitHub
echo git push -u origin main
echo.

echo ================================================================================
echo Diagnostic Complete
echo ================================================================================

echo.
echo If all checks passed, you can now run:
echo setup_github_repository_fixed.bat
echo.
echo If there are errors, please fix them before proceeding.
echo.
pause
