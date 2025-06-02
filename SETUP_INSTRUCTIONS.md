# Setup Instructions for S3 to Snowflake Repository

## What We've Prepared

I've created all the necessary files for your GitHub repository:

### Core Files
- **S3.py** - Updated script with sparkloft dataset support and automated dashboard uploads
- **requirements.txt** - Python dependencies
- **README.md** - Comprehensive documentation
- **.gitignore** - Protects all your credential files (S3.ini, *.ini, tokens, etc.)
- **S3.ini.example** - Template for credentials

### Setup Scripts
- **setup_git_repo.bat** - Windows batch script to initialize Git repo
- **setup_git_repo.ps1** - PowerShell script with better error handling and colors

## Next Steps

### Option 1: Use the Automated Setup (Recommended)

1. **Install Git** (if not already installed):
   - Download from: https://git-scm.com/download/win
   - Or use: `winget install --id Git.Git -e --source winget`

2. **Run the setup script**:
   ```bash
   # Option A: Batch script
   .\setup_git_repo.bat
   
   # Option B: PowerShell script (prettier output)
   .\setup_git_repo.ps1
   ```

### Option 2: Manual Setup

If you prefer to do it manually or the scripts don't work:

```bash
# Initialize repository
git init

# Add remote
git remote add origin https://github.com/Alex-Zeo/S3_to_Snowflake.git

# Add files (credentials will be automatically ignored)
git add .gitignore requirements.txt README.md S3.ini.example S3.py setup_git_repo.*

# Commit
git commit -m "Initial commit: Add S3 upload script with dashboard automation"

# Push to GitHub
git push -u origin main
```

## Security Check ✅

Your credentials are protected by `.gitignore`:
- ✅ S3.ini (contains AWS credentials)
- ✅ All *.ini files 
- ✅ service_account.json
- ✅ token.json
- ✅ All credential and config files

## After Setup

1. **Copy credentials template**:
   ```bash
   copy S3.ini.example S3.ini
   ```

2. **Add your AWS credentials to S3.ini**

3. **Test the upload**:
   ```bash
   python S3.py upload-dashboard --dry-run
   ```

## Features Added to S3.py

- ✅ Added `sparkloft` dataset support
- ✅ New `upload-dashboard` command for automated uploads
- ✅ Predefined file paths for your dashboard files
- ✅ Enhanced documentation and examples

## Repository Structure

```
S3_to_Snowflake/
├── S3.py                    # Main upload script
├── requirements.txt         # Python dependencies  
├── README.md               # Full documentation
├── .gitignore              # Protects credentials
├── S3.ini.example          # Credentials template
├── setup_git_repo.bat      # Windows setup script
├── setup_git_repo.ps1      # PowerShell setup script
└── SETUP_INSTRUCTIONS.md   # This file
```

Once the repository is set up, you can use:
```bash
python S3.py upload-dashboard --dry-run    # Test upload
python S3.py upload-dashboard               # Actual upload
``` 