import logging
import pymssql
import base64
from email_automation.utils import create_lock, remove_lock
from email_automation.api import (
    get_auth_headers, get_emails, get_attachments, 
    mark_as_read, delete_email_from_inbox
)
from email_automation.database import (
    insert_email, insert_attachment, update_email_status,
    mark_emails_deleted, delete_emails_from_db,
    get_emails_to_delete_from_inbox, get_email_status_counts
)

def cmd_scan(config, args):
    """Scan for new emails and add them to the database.
    
    Args:
        config (dict): Configuration settings
        args (Namespace): Command line arguments
    """
    create_lock(config)
    
    try:
        # Get authentication headers
        headers = get_auth_headers(config)
        logging.info("Connected to Microsoft Graph API")
        
        # Database connection parameters
        db_config = config['database']
        
        # Get limit from args or config
        limit = args.limit if args.limit is not None else config.get('defaults', {}).get('scan', {}).get('limit', 50)
        
        # Get days_old from args or config
        days_old = args.days_old if args.days_old is not None else config.get('defaults', {}).get('scan', {}).get('mark_deleted_after_days', 30)
        
        # Test database connection
        with pymssql.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT GETDATE()")
                current_time = cursor.fetchone()[0]
                logging.info(f"Database connection successful! Server time: {current_time}")
        
        # Get unread emails
        unread_emails = get_emails(headers, config, limit=limit, unread_only=True)
        
        if not unread_emails:
            logging.info("No unread emails to process.")
            remove_lock(config)
            return
        
        # Process emails
        with pymssql.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                for idx, email in enumerate(unread_emails, start=1):
                    try:
                        msg_id = email.get('id')
                        sender = email.get('from', {}).get('emailAddress', {}).get('address', '')
                        recipient = config['microsoft']['email_user']
                        subject = email.get('subject', '')
                        body = email.get('body', {}).get('content', '')
                        received_date = email.get('receivedDateTime', '')
                        size = email.get('size', 0)

                        logging.info(f"Processing {idx} of {len(unread_emails)}: {subject} from {sender}")

                        # Insert email if it doesn't exist
                        email_inserted = insert_email(
                            cursor, msg_id, sender, recipient, subject, body, received_date, size
                        )
                        
                        # Skip attachment processing if email already exists
                        if not email_inserted:
                            logging.info(f"Skipping attachments for duplicate email: {subject}")
                            # Still mark as read even if email exists
                            mark_as_read(headers, config, msg_id)
                            continue

                        # Process attachments
                        attachments = get_attachments(headers, config, msg_id)
                        logging.info(f"Found {len(attachments)} attachments")

                        for attachment in attachments:
                            if attachment.get('@odata.type') == '#microsoft.graph.fileAttachment':
                                file_name = attachment['name']
                                file_size = attachment['size']
                                
                                try:
                                    file_data = base64.b64decode(attachment['contentBytes'])
                                    insert_attachment(cursor, msg_id, file_name, file_size, file_data)
                                except Exception as attach_err:
                                    logging.error(f"Error processing attachment {file_name}: {attach_err}")

                        # Mark email as processed in our system
                        update_email_status(cursor, msg_id, 'processed')
                        
                        # Mark as read in Microsoft Graph
                        mark_as_read(headers, config, msg_id)
                    
                    except Exception as email_err:
                        logging.error(f"Error processing email: {email_err}")
                        continue

                # After processing all emails, mark old processed emails as deleted
                if args.auto_mark_deleted:
                    deleted_count = mark_emails_deleted(cursor, days_old=days_old)
                
                conn.commit()
                
                # Show summary
                status_counts = get_email_status_counts(cursor)
                logging.info(f"Email status counts: {status_counts}")
                logging.info("All emails processed and committed.")
    
    except Exception as e:
        logging.exception(f"Error occurred: {e}")
    finally:
        remove_lock(config)

def cmd_delete(config, args):
    """Delete emails based on specified criteria.
    
    Args:
        config (dict): Configuration settings
        args (Namespace): Command line arguments
    """
    create_lock(config)
    
    try:
        # Database connection parameters
        db_config = config['database']
        
        # Get days_old from args or config defaults
        days_old = args.days_old
        
        with pymssql.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                if args.db_only or args.both:
                    # Delete from database
                    emails_deleted, attachments_deleted = delete_emails_from_db(cursor, days_old=days_old)
                    logging.info(f"Deleted {emails_deleted} emails and {attachments_deleted} attachments from database")
                
                if args.email_only or args.both:
                    # Delete from inbox
                    headers = get_auth_headers(config)
                    emails_to_delete = get_emails_to_delete_from_inbox(cursor, days_old=days_old)
                    
                    if not emails_to_delete:
                        logging.info("No emails to delete from inbox")
                    else:
                        deleted_count = 0
                        for msg_id in emails_to_delete:
                            if delete_email_from_inbox(headers, config, msg_id):
                                deleted_count += 1
                        
                        logging.info(f"Deleted {deleted_count} of {len(emails_to_delete)} emails from inbox")
                
                conn.commit()
    except Exception as e:
        logging.exception(f"Error occurred: {e}")
    finally:
        remove_lock(config)

def cmd_status(config, args):
    """Show email status counts.
    
    Args:
        config (dict): Configuration settings
        args (Namespace): Command line arguments
    """
    try:
        # Database connection parameters
        db_config = config['database']
        
        with pymssql.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                status_counts = get_email_status_counts(cursor)
                print("\nEmail Status Counts:")
                print("=====================")
                for status, count in status_counts.items():
                    print(f"{status}: {count}")
                print()
                
                # Get additional statistics if verbose
                if args.verbose:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            MIN(received_date) as oldest,
                            MAX(received_date) as newest,
                            COUNT(DISTINCT sender) as unique_senders
                        FROM emails
                    """)
                    stats = cursor.fetchone()
                    
                    print("Additional Statistics:")
                    print("======================")
                    print(f"Total emails: {stats[0]}")
                    print(f"Oldest email: {stats[1]}")
                    print(f"Newest email: {stats[2]}")
                    print(f"Unique senders: {stats[3]}")
                    print()
    except Exception as e:
        logging.exception(f"Error occurred: {e}")