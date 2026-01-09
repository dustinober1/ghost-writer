#!/usr/bin/env python3
"""
Database restore script for Ghostwriter.

Usage:
    python restore_database.py <backup_file>
    python restore_database.py --from-s3 s3://bucket/path/to/backup.sql.gz
    
Environment variables:
    DATABASE_URL: PostgreSQL connection string
    AWS_ACCESS_KEY_ID: AWS credentials (for S3)
    AWS_SECRET_ACCESS_KEY: AWS credentials (for S3)
"""
import os
import subprocess
import sys
from pathlib import Path
import argparse
import gzip
import tempfile
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


def download_from_s3(s3_path: str, local_path: Path) -> Path:
    """Download backup from S3."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("Error: boto3 not installed. Run: pip install boto3")
        sys.exit(1)
    
    # Parse S3 path
    s3_path = s3_path.replace("s3://", "")
    bucket, key = s3_path.split("/", 1)
    
    s3_client = boto3.client("s3")
    
    print(f"Downloading from s3://{bucket}/{key}")
    
    try:
        s3_client.download_file(bucket, key, str(local_path))
        print(f"Downloaded to: {local_path}")
        return local_path
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        sys.exit(1)


def restore_backup(backup_file: Path, db_config: dict):
    """Restore a PostgreSQL backup using psql."""
    # Decompress if needed
    if str(backup_file).endswith(".gz"):
        print(f"Decompressing: {backup_file}")
        decompressed = backup_file.with_suffix("")
        with gzip.open(backup_file, "rb") as f_in:
            with open(decompressed, "wb") as f_out:
                f_out.write(f_in.read())
        backup_file = decompressed
    
    # Set password environment variable
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]
    
    # Run psql to restore
    cmd = [
        "psql",
        "-h", db_config["host"],
        "-p", str(db_config["port"]),
        "-U", db_config["user"],
        "-d", db_config["database"],
        "-f", str(backup_file),
        "-q",  # Quiet mode
    ]
    
    print(f"Restoring backup to {db_config['database']}...")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error restoring backup: {result.stderr}")
        sys.exit(1)
    
    print("Restore completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Restore Ghostwriter database")
    parser.add_argument("backup_file", nargs="?", help="Path to backup file")
    parser.add_argument("--from-s3", help="S3 path to backup file")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Parse database URL
    db_config = parse_database_url(database_url)
    
    # Determine backup source
    if args.from_s3:
        # Download from S3
        with tempfile.NamedTemporaryFile(suffix=".sql.gz", delete=False) as tmp:
            backup_file = download_from_s3(args.from_s3, Path(tmp.name))
    elif args.backup_file:
        backup_file = Path(args.backup_file)
        if not backup_file.exists():
            print(f"Error: Backup file not found: {backup_file}")
            sys.exit(1)
    else:
        print("Error: Specify backup_file or --from-s3")
        sys.exit(1)
    
    # Confirmation
    if not args.confirm:
        print(f"\nWARNING: This will overwrite the database: {db_config['database']}")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Restore cancelled.")
            sys.exit(0)
    
    # Restore backup
    restore_backup(backup_file, db_config)


if __name__ == "__main__":
    main()
