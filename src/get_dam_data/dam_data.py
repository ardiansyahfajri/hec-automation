import requests
import pandas as pd
from datetime import datetime
import yaml
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Authentication endpoint
AUTH_URL = "https://sinbad.sda.pu.go.id/API/PUB/v1/login/"

# Base URLs for the endpoints
BASE_URL = "https://sinbad.sda.pu.go.id/API/PUB/v1/"
TMA_URL = BASE_URL + "TMA/"
INFLOW_URL = BASE_URL + "INFLOW/"
OUTFLOW_URL = BASE_URL + "OUTFLOW/"

# Path to the configuration YAML file
CONFIG_PATH = "shared/config.yaml"

# Function to authenticate and retrieve token
def authenticate(username, password):
    if not username or not password:
        raise ValueError("Username or Password is not set. Check your configuration file.")

    auth_payload = {"username": username, "password": password}
    response = requests.post(AUTH_URL, data=auth_payload)
    
    if response.status_code == 200:
        token = response.json().get("token")
        if token:
            return token
        else:
            raise ValueError("Authentication successful but no token returned.")
    else:
        raise ConnectionError(f"Failed to authenticate: {response.status_code} {response.text}")

# Function to fetch data from an endpoint
def get_data(endpoint_url, token, dam_id, start_date, end_date):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"id": dam_id, "from": start_date, "until": end_date}
    response = requests.get(endpoint_url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch data from {endpoint_url}: {response.status_code} {response.text}")
        return []

# Function to get today's date range
def get_today_date_range():
    today = datetime.now()
    start_date = today.strftime("%Y-%m-%d 00:00:00")
    end_date = today.strftime("%Y-%m-%d 23:59:59")
    return start_date, end_date

# Function to process and combine the data
def process_data(tma_data, inflow_data, outflow_data):
    # Convert to DataFrames
    tma_df = pd.DataFrame(tma_data)
    inflow_df = pd.DataFrame(inflow_data)
    outflow_df = pd.DataFrame(outflow_data)

    # Validate and process data
    required_columns_tma = ["timestamp", "volume", "tma"]
    required_columns_inflow = ["timestamp", "inflow"]
    required_columns_outflow = [
        "timestamp", "outflow_turbin", "outflow_abaku", 
        "outflow_aindustri", "outflow_irigasi", 
        "outflow_limpas", "outflow_pemeliharaan"
    ]

    # Process outflow data
    outflow_df["outflow"] = (
        outflow_df["outflow_turbin"] +
        outflow_df["outflow_abaku"] +
        outflow_df["outflow_aindustri"] +
        outflow_df["outflow_irigasi"] +
        outflow_df["outflow_limpas"] +
        outflow_df["outflow_pemeliharaan"]
    )
    outflow_df = outflow_df[["timestamp", "outflow"]]

    # Merge the data on the timestamp
    merged_df = pd.merge(tma_df, inflow_df, on="timestamp", how="outer")
    merged_df = pd.merge(merged_df, outflow_df, on="timestamp", how="outer")

    # Drop unnecessary columns like id_x and id_y
    merged_df = merged_df.drop(columns=[col for col in merged_df.columns if col.startswith("id_")], errors="ignore")

    return merged_df

# Main logic
if __name__ == "__main__":
    try:
        # Load configuration
        with open(CONFIG_PATH, "r") as file:
            config = yaml.safe_load(file)

        # Extract shared settings
        shared_config = config.get("shared", {})
        USERNAME = shared_config.get("API_USERNAME")
        PASSWORD = shared_config.get("API_PASSWORD")

        if not USERNAME or not PASSWORD:
            raise ValueError("API_USERNAME or API_PASSWORD is missing in the configuration file.")

        logging.info(f"Loaded credentials: USERNAME={USERNAME}")

        # Authenticate and get token
        token = authenticate(USERNAME, PASSWORD)

        # Get today's date range
        start_date, end_date = get_today_date_range()

        # Extract model settings
        models_config = config.get("models", {})

        # Process each model
        for model_name, model_details in models_config.items():
            logging.info(f"Processing model: {model_name}")

            # Extract the dam ID
            dam_id = model_details.get("dam_id")
            if not dam_id:
                logging.warning(f"No dam_id specified for model: {model_name}. Skipping...")
                continue

            # Ensure output path exists
            output_path = f"data/output/{model_name}/dam_data/"
            os.makedirs(output_path, exist_ok=True)

            logging.info(f"Fetching data for Dam ID: {dam_id}")

            # Fetch TMA, Inflow, and Outflow data
            tma_data = get_data(TMA_URL, token, dam_id, start_date, end_date)
            inflow_data = get_data(INFLOW_URL, token, dam_id, start_date, end_date)
            outflow_data = get_data(OUTFLOW_URL, token, dam_id, start_date, end_date)

            # Process and merge the data
            result_df = process_data(tma_data, inflow_data, outflow_data)

            # Save to CSV
            csv_filename = os.path.join(output_path, f"{model_name}.csv")
            if os.path.exists(csv_filename):
                # Load existing data
                existing_data = pd.read_csv(csv_filename)
                # Append new data
                result_df = pd.concat([existing_data, result_df]).drop_duplicates(subset=["timestamp"])
            
            # Save back to CSV
            result_df.to_csv(csv_filename, index=False)
            logging.info(f"Data for model {model_name} saved to {csv_filename}")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)