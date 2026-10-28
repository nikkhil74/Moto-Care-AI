import os
import sys
import io
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, render_template, send_file

# Set up base directories
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "engine_condition_model.joblib"
DATA_PATH = BASE_DIR / "engine_dataset_downloaded.csv"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MotoCareServer")

# Global model and reference dataset cache
model = None
feature_names = []
dataset_stats = {}

def load_resources():
    global model, feature_names, dataset_stats
    
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found at {MODEL_PATH}")
        return
        
    try:
        model = joblib.load(str(MODEL_PATH))
        if hasattr(model, "feature_names_in_"):
            feature_names = list(model.feature_names_in_)
        else:
            feature_names = [
                "Engine rpm",
                "Lub oil pressure",
                "Fuel pressure",
                "Coolant pressure",
                "lub oil temp",
                "Coolant temp"
            ]
        logger.info(f"Model loaded successfully with features: {feature_names}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")

    # Compute reference stats for sensor threshold analysis
    if DATA_PATH.exists():
        try:
            df = pd.read_csv(str(DATA_PATH))
            for col in feature_names:
                if col in df.columns:
                    s = pd.to_numeric(df[col], errors="coerce").dropna()
                    dataset_stats[col] = {
                        "min": round(float(s.min()), 2),
                        "max": round(float(s.max()), 2),
                        "mean": round(float(s.mean()), 2),
                        "median": round(float(s.median()), 2),
                        "p25": round(float(s.quantile(0.25)), 2),
                        "p75": round(float(s.quantile(0.75)), 2),
                        "std": round(float(s.std()), 2)
                    }
            logger.info("Dataset stats computed successfully.")
        except Exception as e:
            logger.warning(f"Could not compute dataset stats: {e}")

load_resources()

def diagnose_sensor(sensor_name, value):
    """Provide rule-based mechanical advisory based on statistical norms."""
    stats = dataset_stats.get(sensor_name, {})
    median = stats.get("median", 0)
    p25 = stats.get("p25", 0)
    p75 = stats.get("p75", 0)
    min_v = stats.get("min", 0)
    max_v = stats.get("max", 0)

    status = "NORMAL"
    message = "Within nominal operating range."
    risk_factor = 0

    if sensor_name == "Engine rpm":
        if value < 400:
            status = "WARNING"
            message = "RPM is abnormally low (rough idle / stall risk)."
            risk_factor = 1
        elif value > 1600:
            status = "WARNING"
            message = "High engine speed. Sustained high RPM causes thermal stress."
            risk_factor = 1
        else:
            status = "NORMAL"
            message = "Engine RPM is within healthy cruising/idle band."

    elif sensor_name == "Lub oil pressure":
        if value < 1.8:
            status = "CRITICAL"
            message = "Dangerously low oil pressure! Risk of catastrophic engine seizure."
            risk_factor = 3
        elif value > 5.5:
            status = "WARNING"
            message = "High oil pressure. Possible relief valve blockage or cold thick oil."
            risk_factor = 1
        else:
            status = "NORMAL"
            message = "Lubrication oil pressure optimal."

    elif sensor_name == "Fuel pressure":
        if value > 12.0:
            status = "WARNING"
            message = "Fuel pressure is elevated. Possible fuel regulator failure or rich mixture."
            risk_factor = 2
        elif value < 2.5:
            status = "WARNING"
            message = "Low fuel pressure. Possible pump degradation, clogged filter, or fuel starvation."
            risk_factor = 2
        else:
            status = "NORMAL"
            message = "Fuel delivery pressure is stable."

    elif sensor_name == "Coolant pressure":
        if value < 1.0:
            status = "WARNING"
            message = "Low coolant pressure indicates potential system leak or loose cap."
            risk_factor = 2
        elif value > 4.5:
            status = "WARNING"
            message = "Excessive coolant system pressure. Risk of hose burst or head gasket leak."
            risk_factor = 2
        else:
            status = "NORMAL"
            message = "Cooling circuit pressure normal."

    elif sensor_name == "lub oil temp":
        if value > 84.0:
            status = "CRITICAL"
            message = "Oil overheating! Lubrication breakdown and accelerated bearing wear."
            risk_factor = 3
        elif value < 73.0:
            status = "NORMAL"
            message = "Oil warm-up phase / moderate temperature."
        else:
            status = "NORMAL"
            message = "Oil temperature is in the sweet spot."

    elif sensor_name == "Coolant temp":
        if value > 92.0:
            status = "CRITICAL"
            message = "Engine coolant overheating! Risk of head warp or boiling."
            risk_factor = 3
        elif value < 70.0:
            status = "NORMAL"
            message = "Engine below regular running temperature."
        else:
            status = "NORMAL"
            message = "Coolant temperature normal."

    return {
        "status": status,
        "message": message,
        "risk_factor": risk_factor,
        "stats": {
            "min": min_v,
            "max": max_v,
            "median": median,
            "p25": p25,
            "p75": p75
        }
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "features": feature_names,
        "reference_records": 19535
    })

@app.route("/api/stats")
def get_stats():
    return jsonify(dataset_stats)

@app.route("/api/presets")
def get_presets():
    presets = [
        {
            "id": "healthy_cruising",
            "name": "Normal Highway Cruising",
            "description": "Standard optimal running telemetry under moderate highway load.",
            "data": {
                "Engine rpm": 1450.0,
                "Lub oil pressure": 3.45,
                "Fuel pressure": 3.80,
                "Coolant pressure": 2.30,
                "lub oil temp": 76.5,
                "Coolant temp": 78.0
            }
        },
        {
            "id": "critical_low_oil",
            "name": "Severe Low Oil Pressure Alarm",
            "description": "Oil pressure collapses while RPM is idling, threatening cylinder scoring.",
            "data": {
                "Engine rpm": 680.0,
                "Lub oil pressure": 1.15,
                "Fuel pressure": 14.50,
                "Coolant pressure": 3.10,
                "lub oil temp": 84.8,
                "Coolant temp": 83.5
            }
        },
        {
            "id": "overheating_fault",
            "name": "Cooling System Failure & Overheating",
            "description": "Excess coolant temperature and high fuel pressure indicates strain.",
            "data": {
                "Engine rpm": 590.0,
                "Lub oil pressure": 2.80,
                "Fuel pressure": 16.20,
                "Coolant pressure": 4.10,
                "lub oil temp": 86.5,
                "Coolant temp": 98.4
            }
        },
        {
            "id": "fuel_system_strain",
            "name": "Fuel Delivery Anomaly",
            "description": "Elevated fuel pressure with low engine RPM causing rich combustion.",
            "data": {
                "Engine rpm": 520.0,
                "Lub oil pressure": 2.96,
                "Fuel pressure": 18.90,
                "Coolant pressure": 3.70,
                "lub oil temp": 79.5,
                "Coolant temp": 81.2
            }
        },
        {
            "id": "dataset_normal_sample",
            "name": "Verified Dataset Normal Sample (Row #2)",
            "description": "Real engine log from predictive maintenance dataset with 0 (Normal) condition.",
            "data": {
                "Engine rpm": 1221.0,
                "Lub oil pressure": 3.989,
                "Fuel pressure": 6.679,
                "Coolant pressure": 2.214,
                "lub oil temp": 76.401,
                "Coolant temp": 75.669
            }
        }
    ]
    return jsonify(presets)

@app.route("/api/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "ML model is not loaded"}), 500

    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body provided"}), 400

    try:
        # Build input row supporting both direct column names and camelCase / friendly names
        row = {}
        alias_map = {
            "engine_rpm": "Engine rpm",
            "rpm": "Engine rpm",
            "Engine rpm": "Engine rpm",
            
            "lub_oil_pressure": "Lub oil pressure",
            "oil_pressure": "Lub oil pressure",
            "Lub oil pressure": "Lub oil pressure",
            
            "fuel_pressure": "Fuel pressure",
            "Fuel pressure": "Fuel pressure",
            
            "coolant_pressure": "Coolant pressure",
            "Coolant pressure": "Coolant pressure",
            
            "lub_oil_temp": "lub oil temp",
            "oil_temp": "lub oil temp",
            "lub oil temp": "lub oil temp",
            
            "coolant_temp": "Coolant temp",
            "Coolant temp": "Coolant temp"
        }

        for k, v in data.items():
            if k in alias_map:
                try:
                    row[alias_map[k]] = float(v)
                except (ValueError, TypeError):
                    pass

        # Fill defaults from reference dataset median if missing
        for feat in feature_names:
            if feat not in row or row[feat] is None or np.isnan(row[feat]):
                default_val = dataset_stats.get(feat, {}).get("median", 0.0)
                row[feat] = default_val

        input_df = pd.DataFrame([row], columns=feature_names)
        
        pred = int(model.predict(input_df)[0])
        
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(input_df)[0]
            classes = list(model.classes_)
            prob_map = {int(c): float(p) for c, p in zip(classes, probs)}
            prob_normal = prob_map.get(0, 0.5) * 100.0
            prob_fault = prob_map.get(1, 0.5) * 100.0
        else:
            prob_fault = 100.0 if pred == 1 else 0.0
            prob_normal = 100.0 - prob_fault

        # Health score calculation (0 - 100)
        health_score = round(max(0.0, min(100.0, 100.0 - prob_fault)), 1)

        # Risk assessment categorization
        if prob_fault < 30.0:
            risk_level = "LOW"
            risk_label = "Optimal"
            risk_color = "#10b981"
        elif prob_fault < 60.0:
            risk_level = "MODERATE"
            risk_label = "Watchlist"
            risk_color = "#f59e0b"
        elif prob_fault < 85.0:
            risk_level = "HIGH"
            risk_label = "High Risk"
            risk_color = "#f97316"
        else:
            risk_level = "CRITICAL"
            risk_label = "Failure Imminent"
            risk_color = "#ef4444"

        # Diagnostic breakdown for each sensor
        sensor_breakdown = {}
        critical_count = 0
        warning_count = 0
        actions = []

        for feat in feature_names:
            val = row[feat]
            diag = diagnose_sensor(feat, val)
            sensor_breakdown[feat] = {
                "value": val,
                "status": diag["status"],
                "message": diag["message"],
                "stats": diag["stats"]
            }
            if diag["status"] == "CRITICAL":
                critical_count += 1
                actions.append(f"Immediate inspection required for {feat}: {diag['message']}")
            elif diag["status"] == "WARNING":
                warning_count += 1
                actions.append(f"Monitor {feat}: {diag['message']}")

        # Primary conclusion
        if pred == 0:
            condition_title = "Engine Condition: Normal (Healthy)"
            condition_badge = "HEALTHY"
            summary_statement = "All telemetry indicators are consistent with safe and reliable engine performance. Normal maintenance schedule applies."
        else:
            condition_title = "Engine Condition: Fault Detected"
            condition_badge = "FAULT DETECTED"
            summary_statement = "Predictive telemetry model detected sensor anomalies matching engine fault patterns. Preventative servicing recommended."

        if not actions:
            actions = [
                "Continue standard operating procedure and scheduled interval service.",
                "Verify engine oil level at next refueling interval.",
                "Inspect radiator cooling fins for dirt accumulation."
            ]

        response_payload = {
            "prediction": pred,
            "prediction_title": condition_title,
            "prediction_badge": condition_badge,
            "is_fault": (pred == 1),
            "health_score": health_score,
            "probabilities": {
                "normal_pct": round(prob_normal, 2),
                "fault_pct": round(prob_fault, 2)
            },
            "risk": {
                "level": risk_level,
                "label": risk_label,
                "color": risk_color
            },
            "summary": summary_statement,
            "sensors": sensor_breakdown,
            "recommendations": actions,
            "model_metadata": {
                "model_type": type(model.named_steps["model"]).__name__ if hasattr(model, "named_steps") else type(model).__name__,
                "pipeline_steps": [s[0] for s in model.steps] if hasattr(model, "steps") else [],
                "training_features": feature_names
            },
            "bike_info": {
                "model": data.get("bike_model", "Motorcycle"),
                "year": data.get("bike_year", "N/A")
            }
        }

        return jsonify(response_payload)

    except Exception as e:
        logger.exception("Prediction calculation error")
        return jsonify({"error": str(e)}), 500

@app.route("/api/batch-predict", methods=["POST"])
def batch_predict():
    if model is None:
        return jsonify({"error": "ML model is not loaded"}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        df = pd.read_csv(file)
        
        # Check required features
        missing = [f for f in feature_names if f not in df.columns]
        if missing:
            # Try case-insensitive mapping
            lower_map = {c.lower(): c for c in df.columns}
            renames = {}
            for f in feature_names:
                if f.lower() in lower_map:
                    renames[lower_map[f.lower()]] = f
            df = df.rename(columns=renames)
            missing = [f for f in feature_names if f not in df.columns]

        if missing:
            return jsonify({
                "error": f"Uploaded CSV is missing required columns: {missing}. Required columns: {feature_names}"
            }), 400

        X = df[feature_names].copy()
        for col in feature_names:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            median_val = dataset_stats.get(col, {}).get("median", 0.0)
            X[col] = X[col].fillna(median_val)

        preds = model.predict(X)
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            fault_probs = probs[:, 1] * 100.0
        else:
            fault_probs = (preds == 1) * 100.0

        total_rows = len(df)
        fault_count = int(np.sum(preds == 1))
        normal_count = int(np.sum(preds == 0))
        fault_rate = round((fault_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0

        results = []
        for i in range(min(total_rows, 500)):  # Return preview of up to 500 rows
            row_dict = {feat: round(float(X.iloc[i][feat]), 3) for feat in feature_names}
            row_dict["id"] = int(i + 1)
            row_dict["prediction"] = int(preds[i])
            row_dict["status"] = "FAULT" if preds[i] == 1 else "NORMAL"
            row_dict["fault_prob"] = round(float(fault_probs[i]), 1)
            row_dict["health_score"] = round(float(100.0 - fault_probs[i]), 1)
            results.append(row_dict)

        return jsonify({
            "total_rows": total_rows,
            "normal_count": normal_count,
            "fault_count": fault_count,
            "fault_rate_pct": fault_rate,
            "preview_count": len(results),
            "rows": results
        })

    except Exception as e:
        logger.exception("Batch prediction failure")
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500

@app.route("/api/download-sample-csv")
def download_sample_csv():
    sample_path = BASE_DIR / "sample_test_data.csv"
    if sample_path.exists():
        return send_file(
            str(sample_path),
            as_attachment=True,
            download_name="engine_test_sample.csv",
            mimetype="text/csv"
        )
    return jsonify({"error": "Sample file not found"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting MotoCare AI Web Interface at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
