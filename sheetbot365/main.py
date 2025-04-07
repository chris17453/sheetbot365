#!/usr/bin/env python3
import sys
import argparse
import logging
from email_automation.config import load_config
from email_automation.utils import setup_logging
from email_automation.commands import cmd_scan, cmd_delete, cmd_status

def main():
    """Main entry point for the email automation CLI."""
    parser = argparse.ArgumentParser(description='Email Automation System')
    parser.add_argument('--config', '-c', default='/etc/email_automation/config.yaml',
                      help='Path to YAML configuration file (default: /etc/email_automation/config.yaml)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan for new emails and add to database')
    scan_parser.add_argument('--limit', type=int, help='Maximum number of emails to process (overrides config)')
    scan_parser.add_argument('--auto-mark-deleted', action='store_true', help='Automatically mark old processed emails as deleted')
    scan_parser.add_argument('--days-old', type=int, help='Days old threshold for marking as deleted (overrides config)')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete emails from database and/or inbox')
    delete_parser.add_argument('--days-old', type=int, required=True, help='Delete emails older than this many days')
    delete_parser.add_argument('--db-only', action='store_true', help='Delete only from database')
    delete_parser.add_argument('--email-only', action='store_true', help='Delete only from email inbox')
    delete_parser.add_argument('--both', action='store_true', help='Delete from both database and email inbox')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show email status counts')
    status_parser.add_argument('-v', '--verbose', action='store_true', help='Show additional statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Setup logging
        setup_logging(config)
        
        # Execute command
        if args.command == 'scan':
            cmd_scan(config, args)
        elif args.command == 'delete':
            if not any([args.db_only, args.email_only, args.both]):
                delete_parser.error("Must specify at least one of --db-only, --email-only, or --both")
            cmd_delete(config, args)
        elif args.command == 'status':
            cmd_status(config, args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()