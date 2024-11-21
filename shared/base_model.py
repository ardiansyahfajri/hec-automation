import os
import logging
from hms.model import Project

class HECModel:
    def __init__(self, model_name, model_path, forecast_dir, inputs_dir):
        self.model_name = model_name
        self.model_path = model_path
        self.forecast_dir = forecast_dir
        self.inputs_dir = inputs_dir
        self.logger = self.setup_logger()

    def setup_logger(self):
        log_file = os.path.join("logs", f"{self.model_name}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s %(levelname)s:%(message)s"
        )
        return logging.getLogger(self.model_name)

    def update_forecast(self, forecast_file, start_date, end_date):
        """Update forecast parameters in the HEC-HMS file."""
        try:
            with open(forecast_file, "r") as file:
                content = file.readlines()

            for i in range(len(content)):
                if "Start Date" in content[i]:
                    content[i] = f"     Start Date: {start_date}\n"
                elif "End Date" in content[i]:
                    content[i] = f"     End Date: {end_date}\n"

            with open(forecast_file, "w") as file:
                file.writelines(content)

            self.logger.info(f"Updated forecast parameters for {forecast_file}")
        except Exception as e:
            self.logger.error(f"Error updating forecast file {forecast_file}: {e}")
            raise

    def run_model(self):
        """Run the HEC-HMS model."""
        try:
            project = Project.open(self.model_path)
            project.computeForecast()
            project.close()
            self.logger.info(f"Successfully ran HEC-HMS model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Error running HEC-HMS model {self.model_name}: {e}")
            raise
