import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from datetime import datetime, timedelta
import yaml
import matplotlib.pyplot as plt


def load_config(config_path="shared/config.yaml"):
    """Load configuration from a YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def setup_logger(log_file):
    """Set up a logger."""
    import logging
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger()


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


def load_nc_file(nc_path):
    """Load NetCDF file and extract rainfall data."""
    data = Dataset(nc_path)
    rain = data.variables["rain"][:, :, :]  # Adjust variable name if necessary
    time = data.variables["time"][:]
    dates = num2date(time, data.variables["time"].units)
    return rain, dates


def load_thiessen_from_excel(excel_path):
    """Load Thiessen indices and factors from an Excel file."""
    df = pd.read_excel(excel_path)
    indices = list(zip(df["Idx_Lat"], df["Idx_Lon"], df["Faktor_Thi"]))
    return indices


def calculate_thiessen_rain(rain, indices):
    """Calculate Thiessen-weighted rain for specific locations."""
    weighted_rain = np.zeros((rain.shape[0], len(indices)))
    for i, (lat_idx, lon_idx, factor) in enumerate(indices):
        weighted_rain[:, i] = rain[:, lat_idx, lon_idx] * factor
    total_rain = weighted_rain.sum(axis=1)
    return total_rain


def plot_rainfall(rain, dates, output_path, chart_name):
    """Plot and save rainfall chart with adjusted layout for x-axis labels."""
    os.makedirs(output_path, exist_ok=True)
    formatted_dates = [d.strftime("%Y-%m-%d %H:00") for d in dates]
    df = pd.DataFrame({"date": formatted_dates, "rainfall": rain})
    ax = df.plot.bar(x="date", y="rainfall", figsize=(10, 5), color="skyblue")
    plt.grid(axis="y", linewidth=0.2)
    plt.ylabel("Rainfall (mm)")
    plt.xlabel("Time (WIB)")
    plt.title("Rainfall Chart")
    plt.gca().invert_yaxis()
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="center")
    plt.subplots_adjust(bottom=0.35)
    
    # Save the plot
    chart_path = os.path.join(output_path, chart_name)
    plt.savefig(chart_path)
    plt.close()


def main():
    # Load configuration
    config = load_config()
    shared_config = config["shared"]

    for model_name, model_config in config["models"].items():
        # Prepare logger
        log_file = os.path.join(model_config["thiessen_output"], f"{model_name}_thiessen_calculation.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logger = setup_logger(log_file)

        # Prepare file paths
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        today = datetime.now().strftime("%Y%m%d")
        nc_file = find_yesterdays_file(shared_config["raw_folder"], yesterday, logger)

        if not nc_file:
            logger.error(f"No NetCDF file available for {model_name}. Skipping this model.")
            continue

        thiessen_excel = model_config["thiessen_excel"]
        output_path = model_config["thiessen_output"]
        chart_name = f"{model_name}_thiessen_{today}.jpg"

        # Load NetCDF file
        rain, dates = load_nc_file(nc_file)

        # Load Thiessen indices and factors from Excel
        indices = load_thiessen_from_excel(thiessen_excel)

        # Calculate Thiessen rain
        thiessen_rain = calculate_thiessen_rain(rain, indices)

        # Plot rainfall
        plot_rainfall(thiessen_rain, dates, output_path, chart_name)

        logger.info(f"Thiessen rainfall calculation and plotting completed successfully for {model_name}.")


if __name__ == "__main__":
    main()
