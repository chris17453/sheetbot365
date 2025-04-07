# Installation Guide

Follow these steps to install and set up the Email Automation System.

## System Requirements

- Python 3.6 or higher
- MS SQL Server or compatible database
- FreeTDS (for Linux/macOS SQL Server connections)
- Microsoft 365 account with appropriate application permissions

## Installation Steps

### 1. Install FreeTDS (Linux/macOS)

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install freetds-dev freetds-bin
```

#### CentOS/RHEL
```bash
sudo yum install freetds freetds-devel
```

#### macOS
```bash
brew install freetds
```

### 2. Install Python Package

#### Option 1: Install from PyPI
```bash
pip install sheetbot365
```

#### Option 2: Install from source
```bash
git clone https://github.com/chris17453/sheetbot365.git
cd sheetbot365
pip install -e .
```

### 3. Create configuration directory
```bash
sudo mkdir -p /etc/sheetbot365
```

### 4. Copy and edit configuration file
```bash
sudo cp config/config.yaml /etc/sheetbot365/
sudo nano /etc/sheetbot365/config.yaml
```

Update the configuration settings with your:
- Database connection details
- Microsoft Graph API credentials
- Path settings

### 5. Set up database

Create the required database schema using the provided SQL script:

```bash
# Connect to your SQL Server and run the following script
sqlcmd -S your_server -U your_username -P your_password -d your_database -i database/schema.sql
```

Or use the following SQL statements directly:

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

### 6. Create log directory

```bash
sudo mkdir -p /var/log/sheetbot365
sudo chmod 755 /var/log/sheetbot365
```

### 7. Test the installation

```bash
sheetbot365 -c /etc/sheetbot365/config.yaml status
```

If everything is set up correctly, you should see the status of your email database.

## Setting up Microsoft Graph API

1. Register an application in Azure Active Directory
2. Assign appropriate Application permissions:
   - Mail.Read or Mail.ReadWrite
   - User.Read (if needed)
3. Grant admin consent for these permissions
4. Create a client secret
5. Update the config.yaml with:
   - Your tenant ID
   - The application's client ID
   - The client secret value

## Troubleshooting

### Connection Issues

If you're having trouble connecting to SQL Server:

1. Verify FreeTDS configuration
   ```bash
   tsql -C
   ```

2. Test connection using FreeTDS
   ```bash
   tsql -S mssql-email -U webuser -P yourpassword
   ```

3. Check if the server is accessible
   ```bash
   ping your-server-address
   ```

### Authentication Issues

If you're having issues with Microsoft Graph authentication:

1. Verify the credentials in your config file
2. Check that the application has been granted the appropriate permissions
3. Ensure admin consent has been provided for the permissions
4. Check if the client secret has expired (they have limited lifetimes)

### Log Files

Check the log file for detailed error information:
```bash
tail -f /var/log/sheetbot365.log
```