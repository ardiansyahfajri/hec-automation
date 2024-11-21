from datetime import datetime, timedelta
from dotenv import load_dotenv
import ftplib
import os
import logging
import yaml

load_dotenv()

def load_config(config_path="shared/config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, "r") as file:
        config=yaml.safe_load(file)
        
    config['ftp']['username'] = os.getenv("FTP_USERNAME")
    config['ftp']['password'] = os.getenv("FTP_PASSWORD")
    config['ftp']['server'] = os.getenv("FTP_SERVER")
    return config

def setup_logger(log_file="logs/ftp_download.log"):
    """Set up a logger for the script."""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s:%(message)s"
    )
    return logging.getLogger("FTPDownloader")

def download_ftp_files(ftp_config, logger):
    """Download files for the past 7 days and skip already downloaded files."""
    server = ftp_config["server"]
    username = ftp_config["username"]
    password = ftp_config["password"]
    remote_directory = ftp_config["remote_directory"]
    local_directory = ftp_config["local_directory"]

    if not os.path.exists(local_directory):
        os.makedirs(local_directory)

    downloaded_files_log = "logs/downloaded_files.txt"

    # Load previously downloaded files
    if os.path.exists(downloaded_files_log):
        with open(downloaded_files_log, "r") as f:
            downloaded_files = set(f.read().splitlines())
    else:
        downloaded_files = set()

    # Calculate the past 7 days
    today = datetime.now()
    date_list = [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]

    try:
        ftp = ftplib.FTP(server)
        ftp.login(user=username, passwd=password)
        logger.info(f"Connected to FTP server: {server}")

        ftp.cwd(remote_directory)

        files = ftp.nlst()

        for date in date_list:
            preferred_file = f"ECMWF_new_3d.0125.{date}1200.PREC.nc"
            alternate_file = f"ECMWF_new_3d.0125.{date}0000.PREC.nc"

            for file_name in [preferred_file, alternate_file]:
                if file_name in files:
                    if file_name in downloaded_files:
                        logger.info(f"Skipping already downloaded file: {file_name}")
                        continue

                    local_file_path = os.path.join(local_directory, file_name)
                    try:
                        with open(local_file_path, "wb") as local_file:
                            ftp.retrbinary(f"RETR {file_name}", local_file.write)
                        logger.info(f"Downloaded: {file_name}")
                        downloaded_files.add(file_name)
                    except Exception as e:
                        logger.error(f"Error downloading file {file_name}: {e}")
                else:
                    logger.info(f"File not available on FTP: {file_name}")

        with open(downloaded_files_log, "w") as f:
            f.write("\n".join(downloaded_files))

        ftp.quit()
        logger.info("FTP connection closed.")
    except Exception as e:
        logger.error(f"Error during FTP download: {e}")
        raise

def main():
    config = load_config()
    ftp_config = config["ftp"]

    logger = setup_logger()

    download_ftp_files(ftp_config, logger)

if __name__ == "__main__":
    main()
