import requests
import pandas as pd
from datetime import datetime
import yaml
import os

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
    auth_payload = {
        "username": username,
        "password": password
    }
    response = requests.post(AUTH_URL, data=auth_payload)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        print("Failed to authenticate:", response.status_code, response.text)
        exit()

# Function to fetch data from an endpoint
def get_data(endpoint_url, token, dam_id, start_date, end_date):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "id": dam_id,
        "from": start_date,
        "until": end_date
    }
    response = requests.get(endpoint_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {endpoint_url}")
        print(f"Status Code: {response.status_code}, Response: {response.text}")
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

    # Extract relevant fields
    tma_df = tma_df[["timestamp", "volume", "tma"]]
    inflow_df = inflow_df[["timestamp", "inflow"]]
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

    return merged_df

# Main logic
if __name__ == "__main__":
    # Load configuration
    with open(CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)

    # Extract shared settings
    models_config = config["models"]
    username = config["shared"]["username"]
    password = config["shared"]["password"]

    # Authenticate and get token
    token = authenticate(username, password)

    # Get today's date range
    start_date, end_date = get_today_date_range()

    # Process each model
    for model_name, model_details in models_config.items():
        print(f"Processing model: {model_name}")

        # Extract the dam ID
        dam_id = model_details.get("dam_id")
        if not dam_id:
            print(f"No dam_id specified for model: {model_name}. Skipping...")
            continue

        # Ensure output path exists
        output_path = f"data/output/{model_name}/dam_data/"
        os.makedirs(output_path, exist_ok=True)

        print(f"Fetching data for Dam ID: {dam_id}")

        # Fetch TMA, Inflow, and Outflow data
        tma_data = get_data(TMA_URL, token, dam_id, start_date, end_date)
        inflow_data = get_data(INFLOW_URL, token, dam_id, start_date, end_date)
        outflow_data = get_data(OUTFLOW_URL, token, dam_id, start_date, end_date)

        # Process and merge the data
        result_df = process_data(tma_data, inflow_data, outflow_data)

        # Save to CSV
        csv_filename = os.path.join(output_path, f"{model_name}.csv")
        result_df.to_csv(csv_filename, index=False)
        print(f"Data for Dam ID {dam_id} saved to {csv_filename}")
