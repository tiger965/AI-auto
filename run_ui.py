# run_ui.py
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Create a minimal config module
if not os.path.exists(os.path.join(project_root, 'config.py')):
    with open(os.path.join(project_root, 'config.py'), 'w') as f:
        f.write("""
def get_config():
    return {"modules": {"trading": True}}

def get(path, default=None):
    config = get_config()
    parts = path.split('.')
    
    for part in parts:
        if isinstance(config, dict) and part in config:
            config = config[part]
        else:
            return default
            
    return config
""")

# Now run the strategy_monitor script
from ui import strategy_monitor