import os
import logging
import yaml
from datetime import datetime, timedelta
import xarray as xr
import geopandas as gpd
import pandas as pd
import rioxarray
from rasterio.warp import calculate_default_transform, Resampling
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm


def load_config(config_path="shared/config.yaml"):
    """Load configuration from a YAML file."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "shared", "config.yaml"))
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


def create_custom_colormap():
    """Create and return a custom colormap."""
    color_list = ["white", "#C4E1F6", "#FEEE91", "#FF9D3D", "#FF2929"]
    boundaries = [0, 1, 6, 11, 21, 100]
    cmap = ListedColormap(color_list)
    norm = BoundaryNorm(boundaries, ncolors=cmap.N, clip=False)
    return cmap, norm



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



def create_animation(data, title, save_path, extent, basin_shp, cmap, norm, logger):
    """Create and save a rainfall animation with a basin shapefile overlay."""
    try:
        x_dim, y_dim = data.rio.x_dim, data.rio.y_dim
        time_dim = "time"

        crs_proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(figsize=(8, 12), subplot_kw={"projection": crs_proj})

        # Set extent
        ax.set_extent(extent, crs=crs_proj)

        # Display initial frame
        initial_frame = data["rain"].isel({time_dim: 0})
        cax = ax.imshow(
            initial_frame.values,
            cmap=cmap,
            norm=norm,
            origin="upper",
            extent=[
                initial_frame["x"].min(),
                initial_frame["x"].max(),
                initial_frame["y"].min(),
                initial_frame["y"].max(),
            ],
            transform=crs_proj,
        )

        # Plot basin shapefile
        basin_shp.plot(ax=ax, facecolor="none", edgecolor="blue", linewidth=1, transform=crs_proj)

        # Add colorbar below the plot
        cbar_ax = fig.add_axes([0.15, 0.1, 0.7, 0.03])
        fig.colorbar(cax, cax=cbar_ax, orientation='horizontal', label='Rainfall (mm)', boundaries=norm.boundaries, ticks=norm.boundaries)

        # Add longitude and latitude gridlines (only left and bottom)
        gl = ax.gridlines(
            draw_labels=True,
            crs=crs_proj,
            linewidth=0.5,
            color="gray",
            alpha=0.7,
            linestyle="--"
        )
        gl.top_labels = False
        gl.right_labels = False
        gl.left_labels = True
        gl.bottom_labels = True
        gl.xlabel_style = {"fontsize": 10}
        gl.ylabel_style = {"fontsize": 10}

        ax.set_xlabel("Longitude", fontsize=14)
        ax.set_ylabel("Latitude", fontsize=14)
        
        
        def update(frame):
            ax.set_title(
                f"{title}\n{pd.to_datetime(data[time_dim].values[frame]).strftime('%d %B %Y %H:%M')}",
                fontsize=18,
                pad=20
            )
            frame_data = data["rain"].isel({time_dim: frame})
            cax.set_data(frame_data.values)
            return cax,

        # Create the animation
        ani = FuncAnimation(fig, update, frames=len(data[time_dim]), interval=1000, repeat=False)

        # Save animation
        ani.save(save_path, writer="pillow", fps=1)
        plt.close(fig)
        logger.info(f"Animation saved to {save_path}")
    except Exception as e:
        logger.error(f"Failed to create animation: {e}")
        raise


def process_model_rain_animation(model_name, model_config, shared_config, cmap, norm):
    """Generate rainfall animation for a specific model."""
    log_file = os.path.join(model_config["animation_output"], f"{model_name}_animation.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = setup_logger(log_file)

    raw_folder = shared_config.get("raw_folder", "data/raw")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    today = datetime.now().strftime("%Y%m%d")

    data_file = find_yesterdays_file(raw_folder, yesterday, logger)
    if not data_file:
        logger.warning(f"No NetCDF file found for {model_name} on {yesterday}. Skipping animation.")
        return

    output_dir = model_config["animation_output"]
    os.makedirs(output_dir, exist_ok=True)

    save_path = os.path.join(output_dir, f"rainfall_{model_name}_{today}.gif")
    path_clip_shp = model_config["clip_shp"]
    path_basin_shp = model_config["basin_shp"]
    projected_crs = model_config["projected_crs"]

    logger.info(f"Processing rainfall animation for {model_name} using file {data_file}...")

    # Load data and shapefiles
    data = xr.open_dataset(data_file).rio.write_crs("EPSG:4326")

    # Dynamically rename dimensions if needed
    if 'lon' in data.dims and 'lat' in data.dims:
        data = data.rename({'lon': 'x', 'lat': 'y'})
    elif 'longitude' in data.dims and 'latitude' in data.dims:
        data = data.rename({'longitude': 'x', 'latitude': 'y'})

    # Ensure spatial dimensions are set
    data = data.rio.set_spatial_dims(x_dim='x', y_dim='y', inplace=False)

    # Read shapefiles
    shp = gpd.read_file(path_clip_shp).to_crs(data.rio.crs)
    basin_shp = gpd.read_file(path_basin_shp).to_crs("EPSG:4326")

    # Clip data
    clipped_data = data.rio.clip(shp.geometry, shp.crs).rio.reproject(projected_crs)

    # Resample data
    resolution = 2000
    transform, width, height = calculate_default_transform(
        clipped_data.rio.crs,
        clipped_data.rio.crs,
        clipped_data.rio.width,
        clipped_data.rio.height,
        *clipped_data.rio.bounds(),
        resolution=(resolution, resolution),
    )
    resampled_data = clipped_data.rio.reproject(
        clipped_data.rio.crs,
        shape=(height, width),
        transform=transform,
        resampling=Resampling.bilinear,
    ).rio.reproject("EPSG:4326")

    extent = [shp.total_bounds[0], shp.total_bounds[2], shp.total_bounds[1], shp.total_bounds[3]]

    create_animation(resampled_data, f"Rainfall Prediction over {model_name}", save_path, extent, basin_shp, cmap, norm, logger)


def main():
    # Load configuration
    config = load_config()
    models = config["models"]
    shared_config = config["shared"]

    # Set colormap and norm
    cmap, norm = create_custom_colormap()

    # Process rainfall animations for all models
    for model_name, model_config in models.items():
        process_model_rain_animation(model_name, model_config, shared_config, cmap, norm)


if __name__ == "__main__":
    main()
