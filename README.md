# 🏍️ MotoCare AI — Predictive Maintenance Engine Diagnostic Interface

An interactive, production-ready web interface for motorcycle engine health and predictive condition classification using trained Machine Learning models and real-time telemetry sensor analysis.

---

## 📁 Project Directory Structure

Everything is neatly stored in:
`C:\Users\india\Desktop\ml aadi\project\`

```
ml aadi/
└── project/
    ├── app.py                         # Main Flask Web Server & Diagnostic REST API
    ├── streamlit_app.py               # Alternative Streamlit Dashboard
    ├── engine_condition_model.joblib  # Trained scikit-learn 1.6.1 ML Pipeline
    ├── engine_dataset_downloaded.csv  # 19,535 Reference Telemetry Cycles
    ├── sample_test_data.csv           # Ready-to-use CSV for Batch Upload testing
    ├── requirements.txt               # Python package dependencies
    ├── run.bat                        # 1-Click Windows Launcher (Opens Browser)
    ├── run_streamlit.bat              # 1-Click Streamlit Launcher
    ├── README.md                      # Complete Project Documentation
    ├── templates/
    │   └── index.html                 # Modern responsive telemetry dashboard HTML
    └── static/
        ├── css/
        │   └── style.css              # Glassmorphic dark cyber-automotive UI
        └── js/
            └── main.js                # Dual-control sliders, charts, & batch CSV engine
```

---

## 🚀 How to Run the Webpage Interface

### Option 1: One-Click Quick Launch (Recommended)
Simply **double-click** the `run.bat` file inside the `project` folder:
- It launches the Flask diagnostic server at `http://127.0.0.1:5000`
- It automatically opens your default web browser to the dashboard!

### Option 2: Command Line
Open PowerShell or Command Prompt inside the `project` directory and run:
```powershell
C:\Users\india\AppData\Local\Programs\Python\Python311\python.exe app.py
```
Then visit `http://127.0.0.1:5000` in any web browser.

### Option 3: Streamlit Interface
If you prefer the Streamlit dashboard:
- Double click `run_streamlit.bat`, or
- Run:
```powershell
C:\Users\india\AppData\Local\Programs\Python\Python311\Scripts\streamlit.exe run streamlit_app.py
```

---

## ✨ Features

### 1. ⚡ Real-Time Telemetry & Condition Predictor
- Interactive synchronized range sliders and numerical input boxes for all 6 telemetry features:
  1. **Engine Speed (RPM)**: 60 – 2,300 rpm
  2. **Lubrication Oil Pressure**: 0.0 – 7.5 bar
  3. **Fuel Delivery Pressure**: 0.0 – 21.5 bar
  4. **Coolant Pressure**: 0.0 – 7.5 bar
  5. **Lub Oil Temperature**: 70.0 – 92.0 °C
  6. **Coolant Temperature**: 60.0 – 130.0 °C
- Instant prediction output:
  - **Condition Badge**: `HEALTHY (0)` vs `FAULT DETECTED (1)`
  - **Health Index Percentage**: 0.0% – 100.0%
  - **Class Probabilities**: Normal % vs Fault %
  - **Risk Categorization**: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`
  - **Subsystem Breakdown Table**: Compares current measurement with baseline medians
  - **Mechanical Action Items**: Actionable maintenance recommendations based on sensor anomalies

### 2. ⚡ Pre-Configured Telemetry Scenarios
One-click presets to immediately demonstrate model behavior:
- **Normal Highway Cruising**: Optimal balanced parameters (88%+ Healthy)
- **Severe Low Oil Pressure Alarm**: Threatens cylinder scoring (Fault condition)
- **Cooling System Failure & Overheating**: High coolant temperature warning
- **Fuel Delivery Anomaly**: High fuel pressure with rough idle
- **Verified Dataset Sample**: Ground-truth row from the 19,535 records dataset

### 3. 📁 Batch CSV Diagnostic Center
- Drag-and-drop or upload any engine telemetry CSV file
- Evaluates hundreds or thousands of rows through the pipeline in seconds
- Displays fleet summary metrics (Total records, Normal count, Fault count, Fault rate %)
- Interactive results table with color-coded status pills and confidence scores
- **Export Results**: Download the scored dataset as a new CSV file with predictions attached

### 4. 📊 Model Architecture & Statistics Inspector
- Shows detailed dataset distribution percentiles (Min, 25%, Median, Mean, 75%, Max)
- Displays logistic regression pipeline feature weights and formulas
- Summarizes cross-validation performance metrics (F1 Macro, Stratified 5-Fold)

### 5. 🔌 Developer REST API
- `POST /api/predict`: JSON endpoint for telematics / OBD-II integration
- `POST /api/batch-predict`: Multipart CSV evaluation endpoint
- `GET /api/presets`: Returns preconfigured test scenarios
- `GET /api/stats`: Returns dataset statistical distributions
- `GET /api/health`: Service health status check

---

## 🧠 Machine Learning Model Details

- **Dataset**: `mukherjee78/predictive-maintenance-engine-data` (19,535 engine telemetry records)
- **Target Label**: `Engine Condition`
  - `0`: Normal / Healthy operating condition
  - `1`: Fault / Maintenance required
- **Pipeline Architecture**:
  1. `preprocessor`: `ColumnTransformer` containing:
     - `SimpleImputer(strategy='median')`
     - `StandardScaler()`
  2. `model`: `LogisticRegression(class_weight='balanced', max_iter=2000, random_state=42)`
- **Trained with**: `scikit-learn==1.6.1`, `joblib`, `pandas`, `numpy`
