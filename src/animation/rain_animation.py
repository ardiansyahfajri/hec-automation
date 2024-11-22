import os
import logging
import yaml
from datetime import datetime, timedelta
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap

def load_config(config_path="shared/config.yaml"):
    """Load configuration from a YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def setup_logger(log_file="logs/rain_animation.log"):
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

def find_yesterdays_file(raw_folder, yesterday):
    """Find the NetCDF file for yesterday's date in the raw folder."""
    file_patterns = [
        f"ECMWF_new_3d.0125.{yesterday}1200.PREC.nc",
        f"ECMWF_new_3d.0125.{yesterday}0000.PREC.nc",
    ]

    for pattern in file_patterns:
        file_path = os.path.join(raw_folder, pattern)
        if os.path.exists(file_path):
            return file_path
    return None

def create_custom_colormap():
    """Create and return a custom colormap."""
    colors = [
        (0, "blue"),
        (0.5, "green"),
        (1, "yellow"),
        (1.5, "orange"),
        (2, "red"),
    ]
    cmap = LinearSegmentedColormap.from_list("custom_rainfall", [c[1] for c in colors])
    return cmap

def create_rainfall_animation(data_file, output_file, basin_shp, frame_duration):
    """Create and save a rainfall animation with a basin shapefile overlay."""
    try:
        # Open the NetCDF data
        ds = xr.open_dataset(data_file)

        # Extract spatial bounds
        lons = ds["longitude"].values
        lats = ds["latitude"].values

        # Load the basin shapefile
        basin_gdf = gpd.read_file(basin_shp)

        # Create a custom colormap
        colormap = create_custom_colormap()

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot the basin shapefile
        basin_gdf.plot(ax=ax, edgecolor="black", facecolor="none", linewidth=0.5)

        # Initialize the plot with empty data
        img = ax.imshow(
            [[0]], extent=[lons.min(), lons.max(), lats.min(), lats.max()],
            origin="lower", cmap=colormap, animated=True
        )
        plt.colorbar(img, ax=ax, label="Rainfall (mm)")

        # Update function for animation
        def update(frame):
            img.set_array(ds["rainfall"][frame, :, :].values)
            ax.set_title(f"Rainfall Animation - Frame {frame}")
            return img,

        # Create animation
        anim = FuncAnimation(
            fig, update, frames=len(ds["time"]), interval=frame_duration, blit=True
        )

        # Save the animation as a gif
        anim.save(output_file, writer="pillow")
        plt.close(fig)

    except Exception as e:
        raise RuntimeError(f"Failed to create animation: {e}")

def process_model_rain_animation(model_name, model_config):
    """Generate rainfall animation for a specific model."""
    logger = setup_logger()

    # Model-specific paths
    raw_folder = os.path.join(model_config["base_dir"], "raw")
    animation_output = model_config["animation_output"]
    basin_shp = model_config["basin_shp"]

    # Shared settings
    frame_duration = 500  # Hardcoded frame duration for this example

    # Determine yesterday's and today's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    today = datetime.now().strftime('%Y%m%d')

    # Find the input NetCDF file
    data_file = find_yesterdays_file(raw_folder, yesterday)
    if not data_file:
        logger.warning(f"No NetCDF file found for {model_name} on {yesterday}. Skipping animation.")
        return

    # Define output animation file
    output_file = os.path.join(animation_output, f"{model_name}_rainfall_{today}.gif")

    # Ensure output directory exists
    if not os.path.exists(animation_output):
        os.makedirs(animation_output)

    logger.info(f"Processing rainfall animation for {model_name} using file {data_file}...")

    try:
        create_rainfall_animation(
            data_file=data_file,
            output_file=output_file,
            basin_shp=basin_shp,
            frame_duration=frame_duration,
        )
        logger.info(f"Rainfall animation saved to {output_file} for {model_name}.")

    except Exception as e:
        logger.error(f"Error processing rainfall animation for {model_name}: {e}")

def main():
    # Load configuration
    config = load_config()
    models = config["models"]

    # Process rainfall animations for all models
    for model_name, model_config in models.items():
        process_model_rain_animation(model_name, model_config)

if __name__ == "__main__":
    main()
