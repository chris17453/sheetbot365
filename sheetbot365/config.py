import os
import yaml

def load_config(config_file):
    """Load configuration from the specified YAML file.
    
    Args:
        config_file (str): Path to the YAML configuration file
        
    Returns:
        dict: Configuration settings
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the config file cannot be parsed or is missing required sections
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML config file: {e}")
    
    # Validate required sections and keys
    required_sections = ['database', 'microsoft', 'paths']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config file: {section}")
    
    # Setup FreeTDS configuration if present
    if 'freetds' in config:
        setup_freetds(config['freetds'])
    
    return config

def setup_freetds(freetds_config):
    """Setup FreeTDS configuration for MS SQL connections.
    
    Args:
        freetds_config (dict): FreeTDS configuration settings
    """
    freetds_path = os.path.expanduser('~/freetds-email.conf')
    with open(freetds_path, 'w') as f:
        f.write(f"""[mssql-email]
    host = {freetds_config['host']}
    port = {freetds_config['port']}
    tds version = {freetds_config['tds_version']}
    client charset = {freetds_config['client_charset']}
    encryption = {freetds_config['encryption']}
""")
    os.environ['FREETDSCONF'] = freetds_path
    os.environ['TDSVER'] = freetds_config['tds_version']