# Email Automation System

A tool for automatically retrieving, processing, and managing emails from a Microsoft 365 account.

## Features

- Automatically fetch emails from a Microsoft 365 inbox
- Download and store email attachments
- Track email lifecycle (downloaded → processed → deleted)
- Clean up old emails from database and inbox
- Configurable retention periods and processing parameters

## Installation

### From Source

```bash
git clone https://github.com/yourusername/sheetbot365.git
cd sheetbot365
pip install -e .
```

### Using pip

```bash
pip install sheetbot365
```

## Configuration

Create a YAML configuration file with the following structure:

```yaml
# Database connection settings
database:
  server: mssql-email
  user: webuser
  password: 'yourpassword'
  database: email_automation

# FreeTDS configuration (for SQL Server connections)
freetds:
  host: 10.0.0.220
  port: 1433
  tds_version: '7.4'
  client_charset: UTF-8
  encryption: 'off'

# Microsoft Graph API settings
microsoft:
  email_user: user@example.com
  client_id: your-app-client-id
  client_secret: your-app-client-secret
  tenant_id: your-tenant-id

# File paths
paths:
  lock_file: /tmp/email_sync.lock
  log_file: /var/log/email_automation.log

# Default values
defaults:
  scan:
    limit: 50
    mark_deleted_after_days: 30
  delete:
    db_retention_days: 90
    inbox_retention_days: 60
```

Save this file to `/etc/email_automation/config.yaml` or specify a custom location with the `--config` parameter.

## Database Schema

The application expects the following database schema:

```sql
-- Create emails table with message_id as primary key
CREATE TABLE emails (
    message_id VARCHAR(255) PRIMARY KEY,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject NVARCHAR(1000),
    body NVARCHAR(MAX),
    received_date DATETIME NOT NULL,
    size INT,
    downloaded_date DATETIME DEFAULT GETDATE(),
    processed_date DATETIME NULL,
    deleted_date DATETIME NULL,
    status VARCHAR(20) DEFAULT 'downloaded' -- downloaded, processed, deleted
);

-- Create attachments table
CREATE TABLE attachments (
    attachment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    message_id VARCHAR(255) NOT NULL,
    file_name NVARCHAR(255) NOT NULL,
    file_size INT,
    file_data VARBINARY(MAX),
    FOREIGN KEY (message_id) REFERENCES emails(message_id)
);

-- Create indexes for better performance
CREATE INDEX idx_emails_date ON emails(received_date);
CREATE INDEX idx_emails_sender ON emails(sender);
CREATE INDEX idx_emails_status ON emails(status);
CREATE INDEX idx_attachments_messageid ON attachments(message_id);
```

## Usage

### Scanning for Emails

```bash
# Using default config location
sheetbot365 scan

# Using custom config
sheetbot365 -c /path/to/config.yaml scan

# Auto-mark old emails as deleted after processing
sheetbot365 scan --auto-mark-deleted

# Override limit and age threshold
sheetbot365 scan --limit 100 --days-old 45 --auto-mark-deleted
```

### Deleting Emails

```bash
# Delete emails older than 90 days from database only
sheetbot365 delete --days-old 90 --db-only

# Delete emails older than 60 days from inbox only
sheetbot365 delete --days-old 60 --email-only

# Delete emails older than 120 days from both database and inbox
sheetbot365 delete --days-old 120 --both
```

### Checking Status

```bash
# Show basic status counts
sheetbot365 status

# Show detailed statistics
sheetbot365 status --verbose
```

## Setting up as a Cron Job

Add these lines to your crontab (edit with `crontab -e`):

```
# Scan for new emails every hour
0 * * * * /usr/bin/python /path/to/sheetbot365/main.py -c /path/to/config.yaml scan --auto-mark-deleted

# Delete old emails once a week (Sunday at 2am)
0 2 * * 0 /usr/bin/python /path/to/sheetbot365/main.py -c /path/to/config.yaml delete --days-old 90 --both
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.