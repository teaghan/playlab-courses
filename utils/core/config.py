import streamlit as st
import yaml
import os

@st.cache_data
def open_config(config_dir="../../config"):
    """
    Loads all configuration files from the config directory into a nested dictionary.
    
    Args:
        config_dir (str): Path to the configuration directory
    
    Returns:
        dict: Nested dictionary containing all configuration data
    
    Raises:
        FileNotFoundError: If the configuration directory is not found
    """
    config_dir = os.path.join(os.path.dirname(__file__), config_dir)
    if not os.path.exists(config_dir):
        raise FileNotFoundError(f"Configuration directory not found: {config_dir}")
    
    config = {}
    
    # Process all files in the config directory
    for filename in os.listdir(config_dir):
        filepath = os.path.join(config_dir, filename)
        if not os.path.isfile(filepath):
            continue
            
        # Get the base name without extension
        name, ext = os.path.splitext(filename)
        
        # Split name into parts for nested dict (e.g., 'questions_examples' -> ['questions', 'examples'])
        dict_keys = name.split('_')
        
        # Load the file based on its extension
        if ext.lower() == '.yaml':
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)
        elif ext.lower() == '.txt':
            with open(filepath, 'r', encoding='utf-8') as file:
                data = file.read()
        else:
            continue
            
        # Create nested dictionary structure
        current_level = config
        for key in dict_keys[:-1]:
            if key not in current_level:
                current_level[key] = {}
            current_level = current_level[key]
        current_level[dict_keys[-1]] = data
    
    return config
    
def domain_url():
    config = open_config()
    return config["domain"]["url"]