# S3 to Snowflake Data Pipeline

Push local data to S3 to refresh Snowflake for Tableau Dashboards

## Overview

This repository contains scripts for uploading Atlanta GA marketing data files to Symphony's dedicated S3 bucket. The data is organized by dataset and automatically processed for consumption by Snowflake and Tableau dashboards.

## Features

- **Multi-dataset Support**: Upload to different datasets (winistry, sparkloft)
- **Excel Processing**: Automatically converts Excel sheets to individual CSV files
- **Organized Storage**: Files are stored in S3 with structured paths including dataset and date
- **Parallel Processing**: Multi-threaded uploads for improved performance
- **Dry Run Mode**: Test uploads without actually transferring files
- **Credential Security**: Configuration file-based credential management

## Prerequisites

- Python 3.10+
- AWS S3 access credentials
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Alex-Zeo/S3_to_Snowflake.git
cd S3_to_Snowflake
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create your credentials file:
```bash
cp S3.ini.example S3.ini
```

4. Edit `S3.ini` with your AWS credentials:
```bash
cp S3.ini.example S3.ini
```

## Usage

### Upload Predefined Dashboard Files

The simplest way to upload the standard dashboard files:

```bash
# Dry run to see what would be uploaded
python S3.py upload-dashboard --dry-run

# Actually upload the files
python S3.py upload-dashboard

# Upload with verbose logging
python S3.py --verbose upload-dashboard
```

This command automatically uploads:
- **Discover Atlanta KPI Dashboard.xlsx** → winistry dataset
- **Discover Atlanta - Monthly Data Report.xlsx** → sparkloft dataset

### Manual File Upload

Upload specific files or directories to chosen datasets:

```bash
# Upload a single file to winistry dataset
python S3.py upload winistry /path/to/file.xlsx

# Upload a directory to sparkloft dataset
python S3.py upload sparkloft /path/to/directory

# Upload with multiple processes
python S3.py upload winistry /path/to/files --processes 10

# Dry run any upload
python S3.py upload winistry /path/to/files --dry-run
```

### Excel File Processing

When uploading Excel files (.xlsx, .xls):
- Each sheet is automatically converted to CSV format
- Files are uploaded individually with descriptive names
- Example: `dashboard.xlsx` with sheets "Q1", "Q2" becomes:
  - `dashboard_Q1.csv`
  - `dashboard_Q2.csv`

## S3 Structure

Files are organized in S3 with the following structure:

```
symphony-client-shared-atlanta-ga/
├── delivery/
│   ├── dataset=winistry/
│   │   └── status=staged/
│   │       └── delivery-date=2025-06-02/
│   │           ├── file1_sheet1.csv
│   │           └── file1_sheet2.csv
│   └── dataset=sparkloft/
│       └── status=staged/
│           └── delivery-date=2025-06-02/
│               ├── file2_sheet1.csv
│               └── file2_sheet2.csv
```

## Configuration

### S3.ini Format

```ini
[AWS]
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

**⚠️ Important**: Never commit credential files to version control. They are automatically ignored by `.gitignore`.

## Command Reference

### Global Options
- `--verbose, -v`: Enable verbose logging
- `--help`: Show help message

### upload-dashboard Command
- `--processes, -p INTEGER`: Number of processes for parallel upload (default: 3)
- `--dry-run, -n`: Test upload without transferring files

### upload Command
- `dataset`: Choose from `winistry` or `sparkloft`
- `path`: File or directory path to upload
- `--processes, -p INTEGER`: Number of processes for parallel upload (default: 3)
- `--dry-run, -n`: Test upload without transferring files

## Security

- AWS credentials are stored locally in `S3.ini` (never committed)
- All credential files are ignored by Git
- Uses IAM-based authentication for S3 access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with `--dry-run`
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**
   - Ensure `S3.ini` exists in the script directory
   - Check that it contains both access key and secret key

2. **"Access Denied" errors**
   - Verify your AWS credentials are correct
   - Ensure your IAM user has S3 write permissions

3. **Excel processing errors**
   - Ensure `openpyxl` is installed: `pip install openpyxl`
   - Check that Excel files are not password-protected

### Logging

Use the `--verbose` flag to see detailed operation logs:
```bash
python S3.py --verbose upload-dashboard
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 