import os
import logging
import yaml
from datetime import datetime, timedelta
from mil.army.usace.hec.vortex.io import BatchImporter
from mil.army.usace.hec.vortex.geo import WktFactory


def load_config(config_path="shared/config.yaml"):
    """Load configuration from a YAML file."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared", "config.yaml"))
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def setup_logger(log_file):
    """Set up a logger."""
    if not log_file:
        raise ValueError("Log file path is not defined in the configuration.")
    
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


def import_data_for_model(model_name, model_config, shared_config, processed_dates):
    """Import data for a specific model based on its configuration."""
    log_file = model_config["log_file"]
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

    if date_str in processed_dates:
        logger.info("Data for date {} has already been processed.".format(date_str))
        return

    # Locate raw files
    raw_folder = shared_config.get("raw_folder", "data/raw")
    file_patterns = [
        "ECMWF_new_3d.0125.{date}1200.PREC.nc",
        "ECMWF_new_3d.0125.{date}0000.PREC.nc",
    ]
    data_file = None
    for pattern in file_patterns:
        file_path = os.path.abspath(os.path.join(raw_folder, pattern.format(date=date_str)))
        logger.info("Checking file: {}".format(file_path))
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
    variables = ['rain']
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
            .variables(variables) \
            .geoOptions(geo_options) \
            .destination(destination) \
            .writeOptions(write_options) \
            .build()
        my_import.process()
        logger.info("Data import and DSS creation complete for date {}.".format(date_str))

        processed_dates.add(date_str)
        save_processed_dates(model_config["processed_dates_log"], processed_dates)

    except Exception as e:
        logger.error("Error during data import for file {}: {}".format(data_file, e))
        logger.error("Geo options: {}".format(geo_options))
        logger.error("Write options: {}".format(write_options))
        raise


def main():
    # Load configuration
    config = load_config("config.yaml")

    models = config["models"]
    shared_config = config["shared"]

    for model_name, model_config in models.items():
        processed_dates = load_processed_dates(model_config["processed_dates_log"])
        import_data_for_model(model_name, model_config, shared_config, processed_dates)


if __name__ == "__main__":
    main()
