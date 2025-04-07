-- Drop tables if they exist (for clean deployment)
IF OBJECT_ID('attachments', 'U') IS NOT NULL
    DROP TABLE attachments;
IF OBJECT_ID('emails', 'U') IS NOT NULL
    DROP TABLE emails;

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