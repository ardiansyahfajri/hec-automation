import os
import logging
from datetime import datetime, timedelta
from hms.model import Project
from hms import Hms
import yaml

def load_config(config_path):
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


def update_forecast_parameters(file_path, start_date, start_time, forecast_date, forecast_time, end_date, end_time, logger):
    """Update forecast parameters in the HEC-HMS forecast file."""
    try:
        with open(file_path, "r") as file:
            content = file.readlines()

        for i in range(len(content)):
            if "Start Date" in content[i]:
                content[i] = "     Start Date: {}\n".format(start_date)
            elif "Start Time" in content[i]:
                content[i] = "     Start Time: {}\n".format(start_time)
            elif "Forecast Date" in content[i]:
                content[i] = "     Forecast Date: {}\n".format(forecast_date)
            elif "Forecast Time" in content[i]:
                content[i] = "     Forecast Time: {}\n".format(forecast_time)
            elif "End Date" in content[i]:
                content[i] = "     End Date: {}\n".format(end_date)
            elif "End Time" in content[i]:
                content[i] = "     End Time: {}\n".format(end_time)

        with open(file_path, "w") as file:
            file.writelines(content)

        logger.info("Forecast parameters updated successfully for file: {}".format(file_path))
    except Exception as e:
        logger.error("Error updating forecast parameters for file {}: {}".format(file_path, e))
        raise


def get_dynamic_dates():
    """Calculate dynamic dates for forecast parameters."""
    today = datetime.now()
    start_date_dt = today - timedelta(days=1)
    forecast_date_dt = today
    end_date_dt = today + timedelta(days=5)

    start_date = start_date_dt.strftime("%d %B %Y")
    forecast_date = forecast_date_dt.strftime("%d %B %Y")
    end_date = end_date_dt.strftime("%d %B %Y")
    start_date_str = start_date_dt.strftime("%Y%m%d")

    return start_date, forecast_date, end_date, start_date_str


def check_date_in_file(date_str, file_path):
    """Check if a date exists in a file."""
    if not os.path.exists(file_path):
        open(file_path, "a").close()

    with open(file_path, "r") as file:
        dates = [line.strip() for line in file.readlines()]

    return date_str in dates


def append_date_to_file(date_str, file_path):
    """Append a date to a file."""
    with open(file_path, "a") as file:
        file.write("{}\n".format(date_str))


def running_hms(project_path, forecast_name, logger):
    """Run HEC-HMS model for a forecast."""
    try:
        project = Project.open(project_path)
        project.computeForecast(forecast_name)
        project.close()

        logger.info("HEC-HMS model run successfully for forecast: {}".format(forecast_name))
    except Exception as e:
        logger.error("Error running HEC-HMS model for forecast {}: {}".format(forecast_name, e))
        raise


def main():
    config_path = "shared/config.yaml"
    config = load_config(config_path)

    cutoff_hour = 12
    cutoff_minute = 35

    # Process each model
    for model_name, model_config in config["models"].items():
        # Set up logger for each model
        log_file = "logs/{}_forecast.log".format(model_name)
        logger = setup_logger(log_file)

        # Dynamic date calculations
        start_date, forecast_date, end_date, start_date_str = get_dynamic_dates()

        # Paths
        processed_dates_log = model_config["processed_dates_log"]
        forecast_dates_file = "logs/{}_forecast_dates.txt".format(model_name)

        # Check if data has been imported
        if not check_date_in_file(start_date_str, processed_dates_log):
            now = datetime.now()
            cutoff = now.replace(hour=cutoff_hour, minute=cutoff_minute, second=0, microsecond=0)
            if now >= cutoff:
                logger.info("Data for start date {} has not been imported by cutoff time. Skipping run for today.".format(start_date_str))
            else:
                logger.info("Data for start date {} has not been imported yet. Waiting for data.".format(start_date_str))
            continue
        else:
            logger.info("Data for start date {} has been imported.".format(start_date_str))

        # Check if forecast has already been run
        if check_date_in_file(start_date_str, forecast_dates_file):
            logger.info("Forecast has already been run for start date {}. Skipping HEC-HMS run.".format(start_date_str))
            continue
        else:
            logger.info("Forecast has not been run for start date {}. Proceeding to run HEC-HMS.".format(start_date_str))

        # Update forecast parameters and run HEC-HMS model for each forecast
        project_path = model_config["project_path"]
        for forecast_file_path, forecast_name in model_config["forecast_paths"]:
            # Update forecast parameters
            update_forecast_parameters(
                file_path=forecast_file_path,
                start_date=start_date,
                start_time=model_config["start_time"],
                forecast_date=forecast_date,
                forecast_time=model_config["forecast_time"],
                end_date=end_date,
                end_time=model_config["end_time"],
                logger=logger,
            )

            # Run HEC-HMS model
            running_hms(project_path, forecast_name, logger)

        # Append start_date_str to forecast_dates.txt
        append_date_to_file(start_date_str, forecast_dates_file)
        logger.info("Start date {} appended to forecast dates.".format(start_date_str))

    # Shutdown HEC-HMS engine
    Hms.shutdownEngine()


if __name__ == "__main__":
    main()
