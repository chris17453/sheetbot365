import logging
import requests
from msal import ConfidentialClientApplication

def get_auth_headers(config):
    """Get authentication headers for Microsoft Graph API.
    
    Args:
        config (dict): Configuration settings
        
    Returns:
        dict: Headers for API requests
        
    Raises:
        Exception: If authentication fails
    """
    email_user = config['microsoft']['email_user']
    client_id = config['microsoft']['client_id']
    client_secret = config['microsoft']['client_secret']
    tenant_id = config['microsoft']['tenant_id']
    
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    scopes = ['https://graph.microsoft.com/.default']

    app = ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret
    )
    
    token = app.acquire_token_for_client(scopes=scopes)
    if 'access_token' not in token:
        raise Exception(f"Auth failed: {token}")
    
    return {
        'Authorization': f'Bearer {token["access_token"]}',
        'Prefer': 'outlook.body-content-type="text"',
        'Content-Type': 'application/json'
    }

def get_emails(headers, config, limit=100, unread_only=True):
    """Get unread emails from the inbox using Microsoft Graph API with pagination support."""
    email_user = config['microsoft']['email_user']
    all_emails = []
    
    # Build the initial URL with a filter for unread emails if needed
    if unread_only:
        next_link = f'https://graph.microsoft.com/v1.0/users/{email_user}/mailFolders/Inbox/messages?$filter=isRead eq false&$top={min(limit, 1000)}'
    else:
        next_link = f'https://graph.microsoft.com/v1.0/users/{email_user}/mailFolders/Inbox/messages?$top={min(limit, 1000)}'
    
    while next_link and len(all_emails) < limit:
        response = requests.get(next_link, headers=headers)
        
        if response.status_code != 200:
            logging.error(f"Error getting emails: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        emails = data.get('value', [])
        
        if not emails:
            break
            
        all_emails.extend(emails)
        next_link = data.get('@odata.nextLink')
    
    if not all_emails:
        if unread_only:
            logging.warning("No unread emails found in inbox.")
        else:
            logging.warning("No emails found in inbox.")
        return []

    logging.info(f"Found {len(all_emails)} {'unread ' if unread_only else ''}emails in inbox.")
    return all_emails[:limit]

def get_attachments(headers, config, msg_id):
    """Get attachments for a specific email.
    
    Args:
        headers (dict): API request headers
        config (dict): Configuration settings
        msg_id (str): Message ID
        
    Returns:
        list: Attachment objects from the API
    """
    email_user = config['microsoft']['email_user']
    attach_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages/{msg_id}/attachments"
    attach_response = requests.get(attach_url, headers=headers)
    
    if attach_response.status_code != 200:
        logging.error(f"Error getting attachments: {attach_response.status_code} - {attach_response.text}")
        return []
        
    attachments = attach_response.json().get('value', [])
    return attachments

def mark_as_read(headers, config, msg_id):
    """Mark an email as read in Outlook.
    
    Args:
        headers (dict): API request headers
        config (dict): Configuration settings
        msg_id (str): Message ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    email_user = config['microsoft']['email_user']
    patch_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages/{msg_id}"
    mark_read = requests.patch(patch_url, headers=headers, json={"isRead": True})
    
    if mark_read.status_code not in (200, 204):
        logging.warning(f"Failed to mark email as read: {mark_read.status_code} - {mark_read.text}")
        return False
    return True

def delete_email_from_inbox(headers, config, msg_id):
    """Delete an email from the inbox.
    
    Args:
        headers (dict): API request headers
        config (dict): Configuration settings
        msg_id (str): Message ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    email_user = config['microsoft']['email_user']
    delete_url = f"https://graph.microsoft.com/v1.0/users/{email_user}/messages/{msg_id}"
    response = requests.delete(delete_url, headers=headers)
    
    if response.status_code not in (200, 204):
        logging.warning(f"Failed to delete email from inbox: {response.status_code} - {response.text}")
        return False
    return True