
# HEC Automation

This repository contains scripts to automate rainfall visualization, data import, and HEC-HMS hydrological forecasting.

---

### Features
- Generate rainfall animations.
- Import and process forecast data automatically.
- Run HEC-HMS models for hydrological forecasting.

---

### Installation

#### **Clone the Repository**
```bash
git clone https://github.com/ardiansyahfajri/hec-automation.git
cd hec-automation
```

#### **Set Up a Virtual Environment**
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux or Git Bash:
     ```bash
     source venv/bin/activate
     ```

#### **Install Dependencies**
Install the required packages:
```bash
pip install -r requirements.txt
```

---

### Usage

#### **Rainfall Animation**
Run the script to generate rainfall animations:
```bash
python src/animation/rain_animation.py
```

#### **Data Import Automation**
Automate data imports using:
```bash
python src/data_import/import_automation.py
```

#### **HEC-HMS Forecasting**
Run HEC-HMS forecasts with:
```bash
python src/forecast/compute_forecast.py
```

---

### Project Structure
```plaintext
hec-automation/
├── src/
│   ├── animation/         # Scripts for rainfall animation
│   │   └── rain_animation.py
│   ├── data_import/       # Data import and preprocessing scripts
│   │   ├── import_automation.py
│   │   └── ftp_iris_import.py
│   ├── forecast/          # Forecasting-related scripts
│       └── compute_forecast.py
├── logs/                  # Log files (added to .gitignore)
├── data/                  # Data files (added to .gitignore)
├── requirements.txt       # List of dependencies
├── .gitignore             # Ignored files
├── README.md              # Project overview and setup instructions
```

---

### Contributing
1. Fork the repository.
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature-name
   ```
3. Commit and push your changes:
   ```bash
   git commit -m "Add feature-name"
   git push origin feature-name
   ```
4. Open a pull request on GitHub.

---

### License
This project is licensed under the MIT License. See `LICENSE` for details.
