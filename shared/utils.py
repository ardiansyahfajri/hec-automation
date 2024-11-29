import yaml
import os

def load_config(config_path="shared/config.yaml"):
    """Load configuration from a YAML file."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared", "config.yaml"))
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def find_yesterdays_file(raw_folder, yesterday, logger):
    """Find the NetCDF file for yesterday's date in the raw folder."""
    file_patterns = [
        f"ECMWF_new_3d.0125.{yesterday}1200.PREC.nc",
        f"ECMWF_new_3d.0125.{yesterday}0000.PREC.nc",
    ]

    for pattern in file_patterns:
        file_path = os.path.join(raw_folder, pattern)
        logger.info(f"Checking for file: {file_path}")
        if os.path.exists(file_path):
            logger.info(f"File found: {file_path}")
            return file_path

    logger.warning(f"No file found for date {yesterday} in folder {raw_folder}")
    return None