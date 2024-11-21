import os
import logging
import yaml
from datetime import datetime, timedelta
from mil.army.usace.hec.vortex.io import BatchImporter
from mil.army.usace.hec.vortex.geo import WktFactory


def setup_vortex_env(config):
    """Set up environment variables for the Vortex app."""
    vortex_home = config["shared"]["vortex_home"]
    os.environ["VORTEX_HOME"] = vortex_home
    os.environ["PATH"] = f"{vortex_home}/bin;{vortex_home}/bin/gdal;" + os.environ.get("PATH", "")
    os.environ["GDAL_DATA"] = f"{vortex_home}/bin/gdal/gdal-data"
    os.environ["PROJ_LIB"] = f"{vortex_home}/bin/gdal/projlib"
    os.environ["CLASSPATH"] = f"{vortex_home}/lib/*"

def load_config(config_path="config.yaml"):
    """Load configuration from a YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def setup_logger(log_file):
    """Set up a logger."""
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger()

def load_processed_dates(log_file):
    """Load processed dates from a log file."""
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_processed_dates(log_file, processed_dates):
    """Save processed dates to a log file."""
    with open(log_file, "w") as f:
        for date in sorted(processed_dates):
            f.write("{}\n".format(date))

def import_data_for_model(model_name, model_config, shared_config):
    """Import data for a specific model based on its configuration."""
    log_file = model_config["log_file"]
    processed_dates_log = model_config["processed_dates_log"]
    base_dir = model_config["base_dir"]
    clip_shp = model_config["clip_shp"]
    destination = model_config["destination"]
    targetWkt = model_config["targetWkt"]
    partA = model_config["partA"]

    # Set up logging
    logger = setup_logger(log_file)

    # Determine the date to process (yesterday's date)
    now = datetime.now()
    date_to_process = (now - timedelta(days=1)).date()
    date_str = date_to_process.strftime('%Y%m%d')

    # Load processed dates
    processed_dates = load_processed_dates(processed_dates_log)

    if date_str in processed_dates:
        logger.info("Data for date {} has already been processed.".format(date_str))
        return

    # Find the file to process
    file_pattern = [
        "ECMWF_new_3d.0125.{date}1200.PREC.nc",
        "ECMWF_new_3d.0125.{date}0000.PREC.nc",
    ]
    data_file = None
    for pattern in file_pattern:
        file_path = os.path.join(base_dir, pattern.format(date=date_str))
        if os.path.exists(file_path):
            data_file = file_path
            logger.info("Found data file: {}".format(file_path))
            break

    if not data_file:
        current_time = now.time()
        cutoff_time = datetime.strptime(shared_config["data_cutoff_time"], "%H:%M").time()

        if current_time >= cutoff_time:
            logger.warning("No data files available for date {} by cutoff time {}.".format(date_str, cutoff_time))
        else:
            logger.info("Data for date {} not available yet. Will retry later.".format(date_str))
        return

    # Build and execute BatchImporter
    geo_options = {
        "pathToShp": clip_shp,
        "targetCellSize": "2000",
        "targetWkt": WktFactory.fromEpsg(targetWkt),
        "resamplingMethod": "Bilinear",
    }

    write_options = {
        "partA": partA,
        "partB": model_name.upper(),
        "partC": "PRECIPITATION",
        "partF": "ECMWF",
        "dataType": "PER-CUM",
        "units": "mm",
    }

    try:
        my_import = BatchImporter.builder() \
            .inFiles([data_file]) \
            .geoOptions(geo_options) \
            .destination(destination) \
            .writeOptions(write_options) \
            .build()
        my_import.process()
        logger.info("Data import and DSS creation complete for date {}.".format(date_str))

        # Mark date as processed
        processed_dates.add(date_str)
        save_processed_dates(processed_dates_log, processed_dates)

    except Exception as e:
        logger.error("Error during data import for date {}: {}".format(date_str, e))
        raise

def main():
    # Load configuration
    config = load_config("config.yaml")

    # Set up the Vortex environment
    setup_vortex_env(config)

    models = config["models"]
    shared_config = config["shared"]

    # Loop through all models
    for model_name, model_config in models.items():
        import_data_for_model(model_name, model_config, shared_config)

if __name__ == "__main__":
    main()
