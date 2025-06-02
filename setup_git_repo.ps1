# Git Repository Setup Script for S3 to Snowflake
# This script will initialize the repository and push to GitHub

Write-Host "Setting up Git repository for S3 to Snowflake project..." -ForegroundColor Green
Write-Host ""

# Check if git is available
try {
    $gitVersion = git --version 2>$null
    Write-Host "✓ Git is available: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Git is not installed or not available in PATH." -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Initialize repository if not already initialized
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
} else {
    Write-Host "✓ Git repository already exists." -ForegroundColor Green
}

# Configure Git user (you may want to change these)
Write-Host "Configuring Git user..." -ForegroundColor Yellow
git config user.name "Alex-Zeo"
git config user.email "your-email@example.com"

# Add the remote repository
Write-Host "Adding remote repository..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin https://github.com/Alex-Zeo/S3_to_Snowflake.git

# Create and switch to main branch
Write-Host "Setting up main branch..." -ForegroundColor Yellow
git checkout -B main

# Add files to staging
Write-Host "Adding files to Git..." -ForegroundColor Yellow
$filesToAdd = @(
    ".gitignore",
    "requirements.txt", 
    "README.md",
    "S3.ini.example",
    "S3.py",
    "setup_git_repo.bat",
    "setup_git_repo.ps1"
)

foreach ($file in $filesToAdd) {
    if (Test-Path $file) {
        git add $file
        Write-Host "  ✓ Added $file" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Skipped $file (not found)" -ForegroundColor Yellow
    }
}

# Check what will be committed
Write-Host ""
Write-Host "Files to be committed:" -ForegroundColor Cyan
git status --porcelain

# Verify that sensitive files are ignored
Write-Host ""
Write-Host "Checking that sensitive files are properly ignored..." -ForegroundColor Cyan

$sensitiveFiles = @("S3.ini", "*.ini", "service_account.json", "token.json")
$allIgnored = $true

foreach ($file in $sensitiveFiles) {
    if (Test-Path $file) {
        $ignored = git check-ignore $file 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $file is properly ignored" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ WARNING: $file is NOT being ignored!" -ForegroundColor Red
            $allIgnored = $false
        }
    }
}

if (-not $allIgnored) {
    Write-Host "Please check your .gitignore file before proceeding!" -ForegroundColor Red
    $continue = Read-Host "Do you want to continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Commit the changes
Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Yellow

$commitMessage = @"
Initial commit: Add S3 upload script with dashboard automation

- Added S3.py with support for winistry and sparkloft datasets
- Added automated dashboard upload command
- Excel files are automatically converted to CSV sheets
- Comprehensive .gitignore to protect credentials
- Full documentation and examples
"@

git commit -m $commitMessage

# Push to GitHub
Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "  SUCCESS: Repository has been pushed to GitHub!" -ForegroundColor Green
    Write-Host "  URL: https://github.com/Alex-Zeo/S3_to_Snowflake" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Red
    Write-Host "  ERROR: Failed to push to GitHub." -ForegroundColor Red
    Write-Host "  Please check your credentials and try again." -ForegroundColor Red
    Write-Host "====================================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy S3.ini.example to S3.ini" -ForegroundColor Yellow
Write-Host "2. Add your AWS credentials to S3.ini" -ForegroundColor Yellow
Write-Host "3. Test the upload: python S3.py upload-dashboard --dry-run" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit" 