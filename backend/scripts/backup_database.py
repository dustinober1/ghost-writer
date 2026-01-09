#!/usr/bin/env python3
"""
Database backup script for Ghostwriter.
Supports local backups and S3 uploads.

Usage:
    python backup_database.py [--upload-to-s3]
    
Environment variables:
    DATABASE_URL: PostgreSQL connection string
    BACKUP_DIR: Local backup directory (default: ./backups)
    S3_BUCKET: S3 bucket name (required if --upload-to-s3)
    AWS_ACCESS_KEY_ID: AWS credentials
    AWS_SECRET_ACCESS_KEY: AWS credentials
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import argparse
import gzip
import shutil
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


def parse_database_url(url: str) -> dict:
    """Parse PostgreSQL URL into components."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
        "user": parsed.username,
        "password": parsed.password,
    }


def create_backup(db_config: dict, backup_dir: Path) -> Path:
    """Create a PostgreSQL backup using pg_dump."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"ghostwriter_backup_{timestamp}.sql"
    compressed_file = backup_dir / f"ghostwriter_backup_{timestamp}.sql.gz"
    
    # Create backup directory if it doesn't exist
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Set password environment variable
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]
    
    # Run pg_dump
    cmd = [
        "pg_dump",
        "-h", db_config["host"],
        "-p", str(db_config["port"]),
        "-U", db_config["user"],
        "-d", db_config["database"],
        "-F", "p",  # Plain SQL format
        "-f", str(backup_file),
        "--no-owner",
        "--no-acl",
    ]
    
    print(f"Creating backup: {backup_file}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error creating backup: {result.stderr}")
        sys.exit(1)
    
    # Compress the backup
    print(f"Compressing backup: {compressed_file}")
    with open(backup_file, "rb") as f_in:
        with gzip.open(compressed_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Remove uncompressed file
    backup_file.unlink()
    
    # Get file size
    size_mb = compressed_file.stat().st_size / (1024 * 1024)
    print(f"Backup created: {compressed_file} ({size_mb:.2f} MB)")
    
    return compressed_file


def upload_to_s3(file_path: Path, bucket: str, prefix: str = "backups"):
    """Upload backup file to S3."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("Error: boto3 not installed. Run: pip install boto3")
        sys.exit(1)
    
    s3_client = boto3.client("s3")
    s3_key = f"{prefix}/{file_path.name}"
    
    print(f"Uploading to s3://{bucket}/{s3_key}")
    
    try:
        s3_client.upload_file(str(file_path), bucket, s3_key)
        print(f"Upload complete: s3://{bucket}/{s3_key}")
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        sys.exit(1)


def cleanup_old_backups(backup_dir: Path, keep_days: int = 7):
    """Remove backups older than keep_days."""
    cutoff = datetime.utcnow().timestamp() - (keep_days * 86400)
    
    for backup_file in backup_dir.glob("ghostwriter_backup_*.sql.gz"):
        if backup_file.stat().st_mtime < cutoff:
            print(f"Removing old backup: {backup_file}")
            backup_file.unlink()


def verify_backup(backup_file: Path, db_config: dict) -> bool:
    """Verify backup by checking if it can be parsed."""
    print(f"Verifying backup: {backup_file}")
    
    try:
        with gzip.open(backup_file, "rt") as f:
            # Read first few lines to verify it's valid SQL
            header = f.read(1000)
            if "PostgreSQL" in header or "pg_dump" in header:
                print("Backup verification: PASSED")
                return True
    except Exception as e:
        print(f"Backup verification failed: {e}")
    
    print("Backup verification: FAILED")
    return False


def main():
    parser = argparse.ArgumentParser(description="Backup Ghostwriter database")
    parser.add_argument("--upload-to-s3", action="store_true", help="Upload backup to S3")
    parser.add_argument("--cleanup", action="store_true", help="Remove old backups")
    parser.add_argument("--keep-days", type=int, default=7, help="Days to keep backups")
    parser.add_argument("--verify", action="store_true", help="Verify backup integrity")
    args = parser.parse_args()
    
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
    
    # Parse database URL
    db_config = parse_database_url(database_url)
    
    # Create backup
    backup_file = create_backup(db_config, backup_dir)
    
    # Verify backup
    if args.verify:
        if not verify_backup(backup_file, db_config):
            sys.exit(1)
    
    # Upload to S3
    if args.upload_to_s3:
        s3_bucket = os.getenv("S3_BUCKET")
        if not s3_bucket:
            print("Error: S3_BUCKET environment variable not set")
            sys.exit(1)
        upload_to_s3(backup_file, s3_bucket)
    
    # Cleanup old backups
    if args.cleanup:
        cleanup_old_backups(backup_dir, args.keep_days)
    
    print("Backup completed successfully!")


if __name__ == "__main__":
    main()
