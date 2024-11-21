import yaml

def load_config(config_path="shared/config.yaml"):
    """Load configuration from the YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)
