@echo off
REM ===================================================
REM  Git Repository Setup Script
REM  This script will initialize the repository and push to GitHub
REM ===================================================

echo Setting up Git repository for S3 to Snowflake project...
echo.

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed or not available in PATH.
    echo Please install Git from https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b 1
)

REM Initialize repository if not already initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
) else (
    echo Git repository already exists.
)

REM Configure Git user (you may want to change these)
echo Configuring Git user...
git config user.name "Alex-Zeo"
git config user.email "your-email@example.com"

REM Add the remote repository
echo Adding remote repository...
git remote remove origin 2>nul
git remote add origin https://github.com/Alex-Zeo/S3_to_Snowflake.git

REM Create and switch to main branch
echo Setting up main branch...
git checkout -B main

REM Add files to staging
echo Adding files to Git...
git add .gitignore
git add requirements.txt
git add README.md
git add S3.ini.example
git add S3.py
git add setup_git_repo.bat

REM Check what will be committed
echo.
echo Files to be committed:
git status --porcelain

REM Verify that sensitive files are ignored
echo.
echo Checking that sensitive files are properly ignored...
if exist "S3.ini" (
    git check-ignore S3.ini
    if %errorlevel% neq 0 (
        echo WARNING: S3.ini is NOT being ignored! Check your .gitignore file.
        pause
    ) else (
        echo ✓ S3.ini is properly ignored
    )
)

REM Commit the changes
echo.
echo Committing changes...
git commit -m "Initial commit: Add S3 upload script with dashboard automation

- Added S3.py with support for winistry and sparkloft datasets
- Added automated dashboard upload command
- Excel files are automatically converted to CSV sheets
- Comprehensive .gitignore to protect credentials
- Full documentation and examples"

REM Push to GitHub
echo.
echo Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo  SUCCESS: Repository has been pushed to GitHub!
    echo  URL: https://github.com/Alex-Zeo/S3_to_Snowflake
    echo ===================================================
) else (
    echo.
    echo ===================================================
    echo  ERROR: Failed to push to GitHub.
    echo  Please check your credentials and try again.
    echo ===================================================
)

echo.
echo Next steps:
echo 1. Copy S3.ini.example to S3.ini
echo 2. Add your AWS credentials to S3.ini
echo 3. Test the upload: python S3.py upload-dashboard --dry-run
echo.
pause 