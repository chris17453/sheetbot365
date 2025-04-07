import os
import sys
import logging
import psutil

def setup_logging(config, log_level=logging.INFO):
    """Setup logging with configuration.
    
    Args:
        config (dict): Configuration settings
        log_level (int): Logging level
    """
    log_file = config['paths'].get('log_file', '/var/log/email_automation.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

def is_pid_running(pid):
    """Check if a process with the given PID is running.
    
    Args:
        pid (int): Process ID to check
        
    Returns:
        bool: True if the process is running, False otherwise
    """
    return psutil.pid_exists(pid)

def create_lock(config):
    """Create a lock file to prevent multiple instances from running.
    
    Args:
        config (dict): Configuration settings
    """
    lock_file = config['paths']['lock_file']
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            if is_pid_running(pid):
                logging.info(f"Lock file exists and process {pid} is active. Exiting.")
                sys.exit(0)
            else:
                logging.warning("Stale lock file found. Removing.")
                os.remove(lock_file)
        except Exception as e:
            logging.error(f"Error reading lock file: {e}. Removing.")
            os.remove(lock_file)
    
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))
    logging.info(f"Created lock file with PID {os.getpid()}.")

def remove_lock(config):
    """Remove the lock file.
    
    Args:
        config (dict): Configuration settings
    """
    lock_file = config['paths']['lock_file']
    if os.path.exists(lock_file):
        os.remove(lock_file)
        logging.info("Removed lock file.")