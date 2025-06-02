"""
Upload files to Symphony's dedicated S3 bucket for Atlanta, GA.

Requirements:

- AWS CLI (for configuration, though script uses INI now)
- Python 3.10+
- Dependencies:
    - boto3
    - click
    - pandas
    - openpyxl (for Excel support)
- An `S3.ini` file in the same directory as the script with the following format:
    ```ini
    [AWS]
    AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
    ```

Set up:
    If you aren't using uv, install dependencies before running:

    ```bash
    pip install -r requirements.txt
    ```

    Create the `S3.ini` file with your AWS credentials.

Usage:

    With uv:

        ```bash
        uv run s3_upload.py upload winistry /path/to/files/to/upload
        uv run s3_upload.py upload sparkloft /path/to/files/to/upload
        ```

    With standard Python:

        Upload files to the Winistry dataset:

        ```bash
        python S3.py upload winistry /path/to/files/to/upload
        ```

        Upload files to the Sparkloft dataset:

        ```bash
        python S3.py upload sparkloft /path/to/files/to/upload
        ```

        Upload predefined dashboard files:

        ```bash
        python S3.py upload-dashboard
        ```

    Excel File Handling:
        When uploading Excel files (.xlsx), each sheet will be converted to CSV
        and uploaded separately with the sheet name included in the S3 path.

Advanced:

    Get help:

    ```bash
    python S3.py upload --help
    python S3.py upload-dashboard --help
    ```

    Dry run the upload:

    ```bash
    python S3.py upload winistry /path/to/files/to/upload --dry-run
    python S3.py upload-dashboard --dry-run
    ```

    Use more processes:

    ```bash
    python S3.py upload winistry /path/to/files/to/upload --processes 10
    ```

"""
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "boto3",
#     "click",
#     "pandas",
#     "openpyxl",
# ]
# ///

from __future__ import annotations

import configparser
import datetime
import enum
import io
import logging
import multiprocessing.pool as mpp
import sys
from pathlib import Path

import boto3
import click
import pandas as pd

logger = logging.getLogger("s3_uploads")
S3_BUCKET_NAME = "symphony-client-shared-atlanta-ga"
S3_REGION = "us-east-1"
CONFIG_FILE = "S3.ini"

class Dataset(str, enum.Enum):
    WINISTRY = "winistry"
    SPARKLOFT = "sparkloft"

def configure_logging(verbose: bool):
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s | %(message)s', datefmt=r"%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def cli(verbose: bool):
    """Script for delivering Atlanta GA files to a dedicated Symphony S3 Bucket."""
    configure_logging(verbose)

def get_s3_client():
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent / CONFIG_FILE
    if not config_path.exists():
        logger.error(f"Configuration file '{CONFIG_FILE}' not found in {config_path.parent}.")
        sys.exit(1)

    try:
        config.read(config_path)
        aws_access_key_id = config.get('AWS', 'AWS_ACCESS_KEY_ID')
        aws_secret_access_key = config.get('AWS', 'AWS_SECRET_ACCESS_KEY')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        logger.error(f"Error reading '{CONFIG_FILE}': {e}. Ensure it has an [AWS] section with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred reading '{CONFIG_FILE}'", exc_info=e)
        sys.exit(1)

    if not aws_access_key_id or not aws_secret_access_key:
        logger.error(f"AWS credentials not found or incomplete in '{CONFIG_FILE}'. Please check the file.")
        sys.exit(1)

    logger.info(f"Using credentials from '{CONFIG_FILE}' for S3 access.")
    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

def upload_file_to_s3(s3_client, file_path: Path, s3_path: str, dry_run: bool, path_relative_to_parent: Path):
    full_s3_path = f"{s3_path}{path_relative_to_parent.as_posix().lstrip('.').lstrip('/')}"
    try:
        if dry_run:
            logger.info(f"Would upload '{file_path}' to '{full_s3_path}'.")
        else:
            s3_client.upload_file(
                Bucket=S3_BUCKET_NAME,
                Key=full_s3_path,
                Filename=file_path
            )
            logger.info(f"Uploaded '{file_path}' to 's3://{S3_BUCKET_NAME}/{full_s3_path}'.")
    except Exception as e:
        logger.error(f"Error uploading '{file_path}'", exc_info=e, stack_info=True)

def upload_csv_buffer_to_s3(s3_client, buffer, s3_path: str, original_filename: str, sheet_name: str, dry_run: bool):
    base_filename = Path(original_filename).stem
    safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
    full_s3_path = f"{s3_path}{base_filename}_{safe_sheet_name}.csv"
    
    try:
        if dry_run:
            logger.info(f"Would upload sheet '{sheet_name}' from '{original_filename}' to '{full_s3_path}'.")
        else:
            buffer.seek(0)
            s3_client.upload_fileobj(
                Fileobj=buffer,
                Bucket=S3_BUCKET_NAME,
                Key=full_s3_path
            )
            logger.info(f"Uploaded sheet '{sheet_name}' from '{original_filename}' to 's3://{S3_BUCKET_NAME}/{full_s3_path}'.")
    except Exception as e:
        logger.error(f"Error uploading sheet '{sheet_name}' from '{original_filename}'", exc_info=e, stack_info=True)

def is_excel_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in ['.xlsx', '.xls']

def process_excel_file(s3_client, file_path: Path, s3_path: str, dry_run: bool):
    try:
        logger.info(f"Processing Excel file '{file_path}' and uploading individual sheets.")
        
        # Read all sheets
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        
        if not sheet_names:
            logger.warning(f"No sheets found in '{file_path}'.")
            return
        
        logger.info(f"Found {len(sheet_names)} sheets: {', '.join(sheet_names)}")
        
        for sheet_name in sheet_names:
            try:
                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if df.empty:
                    logger.warning(f"Sheet '{sheet_name}' in '{file_path}' is empty. Skipping.")
                    continue
                
                # Create a buffer to hold the CSV data - using BytesIO instead of StringIO
                csv_buffer = io.BytesIO()
                # Convert to CSV (to bytes)
                csv_str = df.to_csv(index=False)
                csv_buffer.write(csv_str.encode('utf-8'))
                
                # Upload the buffer
                upload_csv_buffer_to_s3(
                    s3_client=s3_client,
                    buffer=csv_buffer,
                    s3_path=s3_path,
                    original_filename=file_path.name,
                    sheet_name=sheet_name,
                    dry_run=dry_run
                )
            except Exception as e:
                logger.error(f"Error processing sheet '{sheet_name}' in '{file_path}'", exc_info=e)
    except Exception as e:
        logger.error(f"Error processing Excel file '{file_path}'", exc_info=e, stack_info=True)

@cli.command()
@click.option("--processes", "-p", type=int, default=3, help="Number of processes to use for uploading files.")
@click.option("--dry-run", "-n", is_flag=True, help="Dry run the upload.")
def upload_dashboard(processes: int, dry_run: bool):
    """Upload predefined dashboard files to their respective datasets.
    
    This command uploads:
    - Discover Atlanta KPI Dashboard.xlsx to winistry dataset
    - Discover Atlanta - Monthly Data Report.xlsx to sparkloft dataset
    """
    s3_client = get_s3_client()
    
    # Define the file mappings
    file_mappings = [
        {
            "file_path": r"C:\Users\research\OneDrive - Atlanta Convention & Visitors Bureau\Marketing Dashboard Data\Documents - ACVB Research\Discover Atlanta KPI Dashboard.xlsx",
            "dataset": "winistry",
            "description": "Discover Atlanta KPI Dashboard"
        },
        {
            "file_path": r"C:\Users\research\OneDrive - Atlanta Convention & Visitors Bureau\Marketing Dashboard Data\Documents - ACVB Research\Discover Atlanta - Monthly Data Report.xlsx", 
            "dataset": "sparkloft",
            "description": "Discover Atlanta Monthly Data Report"
        }
    ]
    
    logger.info("Starting predefined dashboard file uploads...")
    
    for mapping in file_mappings:
        file_path = Path(mapping["file_path"])
        dataset = mapping["dataset"]
        description = mapping["description"]
        
        logger.info(f"Processing {description} for {dataset} dataset...")
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            continue
            
        # Create S3 path for this dataset
        s3_path = f"delivery/dataset={dataset}/status=staged/delivery-date={datetime.datetime.now().strftime(r'%Y-%m-%d')}/"
        
        # Process the file (Excel files will be converted to CSV sheets)
        if is_excel_file(file_path):
            logger.info(f"Processing Excel file '{file_path}' for '{dataset}' dataset.")
            process_excel_file(s3_client, file_path, s3_path, dry_run)
        else:
            logger.info(f"Uploading file '{file_path}' for '{dataset}' dataset.")
            upload_file_to_s3(s3_client, file_path, s3_path, dry_run, file_path.relative_to(file_path.parent))
    
    logger.info("Dashboard file uploads completed.")

@cli.command()
@click.argument("dataset", type=click.Choice([d.value for d in Dataset]))
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--processes", "-p", type=int, default=3, help="Number of processes to use for uploading files.")
@click.option("--dry-run", "-n", is_flag=True, help="Dry run the upload.")
def upload(dataset: str, path: Path, processes: int, dry_run: bool):
    """Upload files to a dataset's folder in the S3 bucket using credentials from S3.ini.

    The dataset is the first argument, and the path to the file or folder to upload is the second argument.
    
    When uploading Excel files (.xlsx), each sheet will be converted to CSV and uploaded
    separately with the sheet name included in the S3 path.

    Examples:

        Upload a single file:

        `python s3_upload.py upload winistry /path/to/files/to/upload.txt`

        Upload a directory:

        `python s3_upload.py upload winistry /path/to/files/to/upload`

        Dry run the upload:

        `python s3_upload.py upload winistry /path/to/files/to/upload --dry-run`

        Use more processes:

        `python s3_upload.py upload winistry /path/to/files/to/upload --processes 10`
    """
    s3_client = get_s3_client()
    s3_path = f"delivery/dataset={dataset}/status=staged/delivery-date={datetime.datetime.now().strftime(r'%Y-%m-%d')}/"

    if path.is_dir():
        files = [f for f in path.glob("**/*") if f.is_file()]
        logger.info(f"Uploading {len(files)} files from '{path.resolve()}' for '{dataset}'.")
        
        # Group files by Excel and non-Excel
        excel_files = [f for f in files if is_excel_file(f)]
        regular_files = [f for f in files if not is_excel_file(f)]
        
        logger.info(f"Found {len(excel_files)} Excel files and {len(regular_files)} regular files.")
        
        # Process Excel files
        for excel_file in excel_files:
            process_excel_file(s3_client, excel_file.resolve(), s3_path, dry_run)
        
        # Process regular files using the original method
        if regular_files:
            with mpp.ThreadPool(processes) as pool:
                pool.starmap(
                    upload_file_to_s3,
                    [(s3_client, file.resolve(), s3_path, dry_run, file.resolve().relative_to(path.resolve())) for file in regular_files],
                )
    else:
        if is_excel_file(path):
            logger.info(f"Processing Excel file '{path.resolve()}' for '{dataset}'.")
            process_excel_file(s3_client, path.resolve(), s3_path, dry_run)
        else:
            logger.info(f"Uploading file '{path.resolve()}' for '{dataset}'.")
            upload_file_to_s3(s3_client, path.resolve(), s3_path, dry_run, path.resolve().relative_to(path.parent.resolve()))

if __name__ == "__main__":
    cli()