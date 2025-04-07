import logging

def check_email_exists(cursor, msg_id):
    """Check if an email with the given message ID already exists in the database.
    
    Args:
        cursor: Database cursor
        msg_id (str): Message ID to check
        
    Returns:
        bool: True if the email exists, False otherwise
    """
    cursor.execute("""
        SELECT COUNT(*) FROM emails WHERE message_id = %s
    """, (msg_id,))
    count = cursor.fetchone()[0]
    return count > 0

def insert_email(cursor, msg_id, sender, recipient, subject, body, received_date, size):
    """Insert a new email if it doesn't already exist.
    
    Args:
        cursor: Database cursor
        msg_id (str): Message ID
        sender (str): Sender email address
        recipient (str): Recipient email address
        subject (str): Email subject
        body (str): Email body content
        received_date (str): Date the email was received
        size (int): Email size in bytes
        
    Returns:
        bool: True if inserted, False if already exists
    """
    if check_email_exists(cursor, msg_id):
        logging.info(f"Email already exists (message_id: {msg_id}): {subject}")
        return False
        
    cursor.execute("""
        INSERT INTO emails (
            message_id, sender, recipient, subject, body, received_date, size, 
            downloaded_date, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, GETDATE(), 'downloaded')
    """, (msg_id, sender, recipient, subject, body, received_date, size))
    logging.info(f"Inserted email: {subject} with status 'downloaded'")
    return True

def insert_attachment(cursor, msg_id, file_name, file_size, file_data):
    """Insert an attachment for an email.
    
    Args:
        cursor: Database cursor
        msg_id (str): Message ID
        file_name (str): Attachment filename
        file_size (int): Attachment size in bytes
        file_data (bytes): Attachment binary data
    """
    cursor.execute("""
        INSERT INTO attachments (message_id, file_name, file_size, file_data)
        VALUES (%s, %s, %s, %s)
    """, (msg_id, file_name, file_size, file_data))
    logging.info(f"Saved attachment: {file_name} ({file_size} bytes)")

def update_email_status(cursor, msg_id, status):
    """Update the status of an email.
    
    Args:
        cursor: Database cursor
        msg_id (str): Message ID
        status (str): New status ('downloaded', 'processed', or 'deleted')
        
    Returns:
        bool: True if updated, False if not found
    """
    status_field = f"{status}_date"
    
    cursor.execute(f"""
        UPDATE emails 
        SET status = %s, {status_field} = GETDATE()
        WHERE message_id = %s
    """, (status, msg_id))
    affected = cursor.rowcount
    if affected > 0:
        logging.info(f"Updated email {msg_id} status to '{status}'")
    return affected > 0

def mark_emails_deleted(cursor, days_old=30):
    """Mark emails as deleted if they are older than the specified number of days.
    
    Args:
        cursor: Database cursor
        days_old (int): Number of days threshold
        
    Returns:
        int: Number of emails marked as deleted
    """
    cursor.execute("""
        UPDATE emails
        SET status = 'deleted', deleted_date = GETDATE()
        WHERE status = 'processed'
          AND processed_date < DATEADD(day, -%s, GETDATE())
          AND deleted_date IS NULL
    """, (days_old,))
    rows_affected = cursor.rowcount
    if rows_affected > 0:
        logging.info(f"Marked {rows_affected} emails as 'deleted'")
    return rows_affected

def delete_emails_from_db(cursor, days_old=90):
    """Permanently delete emails from database that have been in 'deleted' status for more than X days.
    
    Args:
        cursor: Database cursor
        days_old (int): Number of days threshold
        
    Returns:
        tuple: (number of emails deleted, number of attachments deleted)
    """
    # First, delete the attachments
    cursor.execute("""
        DELETE FROM attachments
        WHERE message_id IN (
            SELECT message_id FROM emails
            WHERE status = 'deleted'
            AND DATEDIFF(day, deleted_date, GETDATE()) > %s
        )
    """, (days_old,))
    attachments_deleted = cursor.rowcount
    logging.info(f"Deleted {attachments_deleted} attachments from database")
    
    # Then, delete the emails
    cursor.execute("""
        DELETE FROM emails
        WHERE status = 'deleted'
        AND DATEDIFF(day, deleted_date, GETDATE()) > %s
    """, (days_old,))
    emails_deleted = cursor.rowcount
    logging.info(f"Deleted {emails_deleted} emails from database")
    
    return emails_deleted, attachments_deleted

def get_emails_to_delete_from_inbox(cursor, days_old=90):
    """Get list of emails that should be deleted from inbox.
    
    Args:
        cursor: Database cursor
        days_old (int): Number of days threshold
        
    Returns:
        list: Message IDs to delete
    """
    cursor.execute("""
        SELECT message_id FROM emails
        WHERE status = 'deleted'
        AND DATEDIFF(day, deleted_date, GETDATE()) > %s
    """, (days_old,))
    return [row[0] for row in cursor.fetchall()]

def get_email_status_counts(cursor):
    """Get counts of emails in each status.
    
    Args:
        cursor: Database cursor
        
    Returns:
        dict: Status counts with status as key and count as value
    """
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM emails
        GROUP BY status
        ORDER BY status
    """)
    results = cursor.fetchall()
    
    stats = {}
    for status, count in results:
        stats[status] = count
        
    return stats