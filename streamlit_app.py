import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="MotoCare AI — Predictive Maintenance",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "engine_condition_model.joblib"
DATA_PATH = BASE_DIR / "engine_dataset_downloaded.csv"

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38bdf8;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #111827;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px;
        border-radius: 12px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🏍️ MotoCare AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Motorcycle Predictive Maintenance & Engine Condition Assessment Interface</div>', unsafe_allow_html=True)

if not MODEL_PATH.exists():
    st.error(f"Model file not found at {MODEL_PATH}. Ensure engine_condition_model.joblib is in the directory.")
    st.stop()

if not DATA_PATH.exists():
    st.error(f"Reference dataset not found at {DATA_PATH}. Ensure engine_dataset_downloaded.csv is present.")
    st.stop()

@st.cache_resource
def load_model(path):
    return joblib.load(path)

@st.cache_data
def load_reference_data(path):
    return pd.read_csv(path)

try:
    model = load_model(str(MODEL_PATH))
    reference = load_reference_data(str(DATA_PATH))
except Exception as e:
    st.error(f"Error loading model or data: {e}")
    st.stop()

# Feature identification
if hasattr(model, "feature_names_in_"):
    features = list(model.feature_names_in_)
else:
    features = [
        "Engine rpm",
        "Lub oil pressure",
        "Fuel pressure",
        "Coolant pressure",
        "lub oil temp",
        "Coolant temp"
    ]

# Sidebar
st.sidebar.image("https://img.icons8.com/color/96/motorcycle.png", width=72)
st.sidebar.title("MotoCare Telematics")
st.sidebar.markdown("---")
st.sidebar.subheader("Motorcycle Profile")
bike_model = st.sidebar.text_input("Motorcycle Model", value="Yamaha MT-15 V2")
bike_year = st.sidebar.number_input("Manufacturing Year", min_value=1980, max_value=2030, value=2023)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Scenario Presets")
preset_choice = st.sidebar.selectbox(
    "Load Scenario",
    [
        "Default Medians",
        "Normal Highway Cruising",
        "Low Oil Pressure Alert",
        "Overheating Condition",
        "Fuel System Pressure Spike"
    ]
)

preset_values = {}
if preset_choice == "Normal Highway Cruising":
    preset_values = {
        "Engine rpm": 1450.0,
        "Lub oil pressure": 3.45,
        "Fuel pressure": 3.80,
        "Coolant pressure": 2.30,
        "lub oil temp": 76.5,
        "Coolant temp": 78.0
    }
elif preset_choice == "Low Oil Pressure Alert":
    preset_values = {
        "Engine rpm": 680.0,
        "Lub oil pressure": 1.15,
        "Fuel pressure": 14.50,
        "Coolant pressure": 3.10,
        "lub oil temp": 84.8,
        "Coolant temp": 83.5
    }
elif preset_choice == "Overheating Condition":
    preset_values = {
        "Engine rpm": 590.0,
        "Lub oil pressure": 2.80,
        "Fuel pressure": 16.20,
        "Coolant pressure": 4.10,
        "lub oil temp": 86.5,
        "Coolant temp": 98.4
    }
elif preset_choice == "Fuel System Pressure Spike":
    preset_values = {
        "Engine rpm": 520.0,
        "Lub oil pressure": 2.96,
        "Fuel pressure": 18.90,
        "Coolant pressure": 3.70,
        "lub oil temp": 79.5,
        "Coolant temp": 81.2
    }

st.subheader("Engine Sensor Measurements")
st.caption("Adjust sliders or enter values to test engine predictive telemetry.")

input_values = {}
numeric_features = reference[features].select_dtypes(include=np.number).columns.tolist()

col1, col2 = st.columns(2)

for idx, col in enumerate(features):
    target_col = col1 if idx % 2 == 0 else col2
    with target_col:
        series = pd.to_numeric(reference[col], errors="coerce").dropna()
        min_v = float(series.min())
        max_v = float(series.max())
        med_v = float(series.median())

        default_v = preset_values.get(col, med_v)

        if col == "Engine rpm":
            input_values[col] = st.slider(
                f"⚙️ {col} (rpm)",
                min_value=int(min_v),
                max_value=int(max_v),
                value=int(default_v),
                step=10,
                help=f"Dataset Median: {med_v:.1f} rpm"
            )
        elif "temp" in col.lower():
            input_values[col] = st.slider(
                f"🌡️ {col} (°C)",
                min_value=float(round(min_v, 1)),
                max_value=float(round(max_v, 1)),
                value=float(round(default_v, 1)),
                step=0.1,
                help=f"Dataset Median: {med_v:.2f} °C"
            )
        else:
            input_values[col] = st.slider(
                f"📊 {col} (bar)",
                min_value=float(round(min_v, 2)),
                max_value=float(round(max_v, 2)),
                value=float(round(default_v, 2)),
                step=0.01,
                help=f"Dataset Median: {med_v:.2f} bar"
            )

st.markdown("---")

if st.button("🔍 Run Engine Diagnostic Assessment", type="primary", use_container_width=True):
    input_df = pd.DataFrame([input_values], columns=features)
    
    try:
        prediction = int(model.predict(input_df)[0])
        
        st.subheader("Diagnostic Telemetry Results")
        
        res1, res2, res3 = st.columns(3)
        
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(input_df)[0]
            classes = list(model.classes_)
            prob_map = {int(c): float(p) for c, p in zip(classes, probs)}
            prob_normal = prob_map.get(0, 0.5) * 100.0
            prob_fault = prob_map.get(1, 0.5) * 100.0
        else:
            prob_fault = 100.0 if prediction == 1 else 0.0
            prob_normal = 100.0 - prob_fault
            
        with res1:
            if prediction == 0:
                st.success("✅ Condition: Normal / Healthy (0)")
            else:
                st.error("⚠️ Condition: Fault Detected (1)")
                
        with res2:
            st.metric("Health Index", f"{round(100.0 - prob_fault, 1)}%", delta=f"{round(prob_normal - 50, 1)}%")
            
        with res3:
            st.metric("Fault Probability", f"{round(prob_fault, 1)}%")

        st.markdown("#### Probability Distribution")
        prob_df = pd.DataFrame({
            "Engine Condition": ["Normal (0)", "Fault Detected (1)"],
            "Probability (%)": [prob_normal, prob_fault]
        })
        st.bar_chart(prob_df.set_index("Engine Condition"))

        st.markdown("#### Submitted Telemetry Snapshot")
        st.dataframe(input_df, use_container_width=True)

        if prediction == 1:
            st.warning("⚠️ Telemetry matches predictive failure signatures. Check oil levels, fuel pressure regulator, and cooling systems.")
        else:
            st.info("ℹ️ Telemetry indicates standard operating envelope. Regular maintenance intervals apply.")

    except Exception as e:
        st.error(f"Prediction failed: {e}")

st.markdown("---")
st.caption("MotoCare AI | Predictive Maintenance for Motorcycle Engines | Powered by scikit-learn & Streamlit")
