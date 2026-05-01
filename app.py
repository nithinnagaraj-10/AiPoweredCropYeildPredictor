import os
import pickle
from datetime import datetime
import json

import pandas as pd
import streamlit as st
import plotly.express as px


BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "crop_model.pkl")
DATA_PATH = os.path.join(BASE, "data.csv")


CROP_PROFILES = {
    "Rice": {
        "rainfall": (1200, 2000),
        "temperature": (22, 35),
        "soil_nutrients": (55, 100),
        "badge": "Water-loving",
    },
    "Wheat": {
        "rainfall": (400, 900),
        "temperature": (12, 25),
        "soil_nutrients": (45, 85),
        "badge": "Cool-season",
    },
    "Maize": {
        "rainfall": (500, 1200),
        "temperature": (18, 32),
        "soil_nutrients": (40, 80),
        "badge": "Adaptive",
    },
    "Cotton": {
        "rainfall": (500, 1000),
        "temperature": (20, 35),
        "soil_nutrients": (45, 85),
        "badge": "Heat-tolerant",
    },
    "Soybean": {
        "rainfall": (450, 1000),
        "temperature": (18, 30),
        "soil_nutrients": (50, 90),
        "badge": "Protein crop",
    },
    "Sugarcane": {
        "rainfall": (1000, 1800),
        "temperature": (20, 35),
        "soil_nutrients": (60, 100),
        "badge": "High-yield",
    },
}


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #f2f6f4 0%, #edf5f1 40%, #f9fbfa 100%);
            color: #14221d;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 1.5rem;
            max-width: 1150px;
        }
        .hero-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(27, 72, 54, 0.16);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            backdrop-filter: blur(7px);
            box-shadow: 0 10px 30px rgba(20, 34, 29, 0.08);
        }
        .kpi {
            background: #ffffff;
            border: 1px solid #deebe3;
            border-radius: 14px;
            padding: 0.8rem 0.9rem;
        }
        .kpi-title {
            font-size: 0.78rem;
            color: #5a6a63;
        }
        .kpi-value {
            font-size: 1.24rem;
            font-weight: 700;
            color: #0f4933;
            margin-top: 0.2rem;
        }
        .insight {
            border-left: 4px solid #0f6b46;
            background: #f2f9f5;
            padding: 0.75rem 0.9rem;
            border-radius: 8px;
            color: #234338;
            margin-bottom: 0.55rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not found. Run `python model.py` first.")
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=["rainfall", "temperature", "soil_nutrients", "yield"])
    return pd.read_csv(DATA_PATH)


def score_feature(value, low, high):
    if low <= value <= high:
        return 1.0
    span = max(high - low, 1e-6)
    if value < low:
        return max(0.0, 1 - ((low - value) / span))
    return max(0.0, 1 - ((value - high) / span))


def crop_ranking(rainfall, temperature, nutrients):
    rows = []
    for crop, p in CROP_PROFILES.items():
        r = score_feature(rainfall, *p["rainfall"])
        t = score_feature(temperature, *p["temperature"])
        n = score_feature(nutrients, *p["soil_nutrients"])
        suitability = (0.4 * r + 0.35 * t + 0.25 * n) * 100
        rows.append(
            {
                "Crop": crop,
                "Suitability %": round(suitability, 1),
                "Profile": p["badge"],
            }
        )
    out = pd.DataFrame(rows).sort_values("Suitability %", ascending=False).reset_index(drop=True)
    return out


def classify_yield(yield_value):
    if yield_value < 2500:
        return "Low", "Improve irrigation and nutrient plan."
    if yield_value < 3500:
        return "Moderate", "Good baseline. Fine-tune nutrients for gains."
    if yield_value < 4500:
        return "Good", "Strong output potential. Keep consistent practices."
    return "Excellent", "Near-optimal setup. Focus on disease prevention."


def readiness_score(rainfall, temperature, nutrients):
    # Lightweight "standout" score from model input balance.
    rain_norm = min(rainfall / 1400, 1.2)
    temp_opt = max(0.0, 1 - abs(26 - temperature) / 20)
    nut_norm = min(nutrients / 80, 1.2)
    return round(min(100, (rain_norm * 0.35 + temp_opt * 0.35 + nut_norm * 0.30) * 100), 1)


def predict(model, rainfall, temperature, nutrients):
    df = pd.DataFrame(
        [[rainfall, temperature, nutrients]],
        columns=["rainfall", "temperature", "soil_nutrients"],
    )
    return float(model.predict(df)[0])


def scenario_table(model, base_r, base_t, base_n):
    scenarios = [
        ("Current", base_r, base_t, base_n),
        ("Dry Spell", max(base_r - 250, 0), base_t + 1.5, max(base_n - 5, 0)),
        ("Optimized Plan", base_r + 150, max(base_t - 1.0, 0), min(base_n + 10, 100)),
    ]
    rows = []
    for name, r, t, n in scenarios:
        y = predict(model, r, t, n)
        rows.append(
            {
                "Scenario": name,
                "Rainfall": round(r, 1),
                "Temperature": round(t, 1),
                "Soil Nutrients": round(n, 1),
                "Predicted Yield (kg/ha)": round(y, 1),
            }
        )
    return pd.DataFrame(rows)


def build_report(payload):
    return (
        "Crop Intelligence Report\n"
        "========================\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Inputs:\n"
        f"- Rainfall: {payload['rainfall']} mm\n"
        f"- Temperature: {payload['temperature']} C\n"
        f"- Soil Nutrients: {payload['nutrients']}\n\n"
        f"Predicted Yield: {payload['predicted_yield']} kg/ha\n"
        f"Category: {payload['category']}\n"
        f"Readiness Score: {payload['readiness']} / 100\n\n"
        f"Top Crop Match: {payload['top_crop']}\n"
        f"Top Suitability: {payload['top_suitability']}%\n\n"
        "Scenario Summary:\n"
        f"{payload['scenario_json']}\n"
    )


def main():
    st.set_page_config(page_title="Crop Intelligence Studio", page_icon="🌱", layout="wide")
    inject_styles()

    st.markdown(
        """
        <div class="hero-card">
            <h2 style="margin:0; color:#173328;">Crop Intelligence Studio</h2>
            <p style="margin:0.3rem 0 0 0; color:#4e6058;">
                Minimal UI, premium presentation, and insight-first crop planning.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    model = load_model()
    data = load_data()

    left, right = st.columns([0.95, 1.35], gap="large")
    with left:
        st.subheader("Input Panel")
        rainfall = st.slider("Rainfall (mm)", min_value=0.0, max_value=2000.0, value=900.0, step=10.0)
        temperature = st.slider("Temperature (C)", min_value=0.0, max_value=50.0, value=25.0, step=0.5)
        nutrients = st.slider("Soil Nutrients (0-100)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)
        focus_crop = st.selectbox("Focus Crop", list(CROP_PROFILES.keys()), index=0)

        run = st.button("Run Smart Analysis", type="primary", use_container_width=True)
        if not run and "result" not in st.session_state:
            st.info("Set values and click **Run Smart Analysis**.")
            return

    if run or "result" in st.session_state:
        predicted_yield = round(predict(model, rainfall, temperature, nutrients), 1)
        category, advice = classify_yield(predicted_yield)
        ready = readiness_score(rainfall, temperature, nutrients)
        ranking = crop_ranking(rainfall, temperature, nutrients)
        scenarios = scenario_table(model, rainfall, temperature, nutrients)

        st.session_state["result"] = {
            "predicted_yield": predicted_yield,
            "category": category,
            "advice": advice,
            "ready": ready,
            "ranking": ranking,
            "scenarios": scenarios,
            "focus_crop": focus_crop,
        }

    result = st.session_state["result"]
    ranking = result["ranking"]
    scenarios = result["scenarios"]
    top = ranking.iloc[0]
    focus_row = ranking[ranking["Crop"] == result["focus_crop"]].iloc[0]

    with right:
        k1, k2, k3 = st.columns(3)
        k1.markdown(
            f"<div class='kpi'><div class='kpi-title'>Predicted Yield</div><div class='kpi-value'>{result['predicted_yield']:,.0f} kg/ha</div></div>",
            unsafe_allow_html=True,
        )
        k2.markdown(
            f"<div class='kpi'><div class='kpi-title'>Yield Category</div><div class='kpi-value'>{result['category']}</div></div>",
            unsafe_allow_html=True,
        )
        k3.markdown(
            f"<div class='kpi'><div class='kpi-title'>Field Readiness</div><div class='kpi-value'>{result['ready']}/100</div></div>",
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown(f"<div class='insight'><b>Top matched crop:</b> {top['Crop']} ({top['Suitability %']}%)</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='insight'><b>Focus crop fit:</b> {result['focus_crop']} at {focus_row['Suitability %']}% suitability</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='insight'><b>Mentor note:</b> {result['advice']}</div>", unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.2, 1.0], gap="large")

    with c1:
        st.subheader("Crop Raceboard")
        fig_rank = px.bar(
            ranking,
            x="Suitability %",
            y="Crop",
            color="Suitability %",
            color_continuous_scale="Greens",
            orientation="h",
            text="Suitability %",
        )
        fig_rank.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_rank, use_container_width=True)
        st.dataframe(ranking, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Scenario Lab")
        fig_sc = px.line(
            scenarios,
            x="Scenario",
            y="Predicted Yield (kg/ha)",
            markers=True,
            line_shape="spline",
        )
        fig_sc.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_sc, use_container_width=True)
        st.dataframe(scenarios, use_container_width=True, hide_index=True)

    st.write("")
    st.subheader("Standout Features Added")
    st.markdown(
        "- Multi-crop suitability ranking with an easy visual raceboard\n"
        "- Scenario simulation: Current vs Dry Spell vs Optimized Plan\n"
        "- Field readiness score for presentation-friendly quick judgment\n"
        "- Downloadable report for mentor demo and submission"
    )

    payload = {
        "rainfall": rainfall,
        "temperature": temperature,
        "nutrients": nutrients,
        "predicted_yield": result["predicted_yield"],
        "category": result["category"],
        "readiness": result["ready"],
        "top_crop": top["Crop"],
        "top_suitability": top["Suitability %"],
        "scenario_json": json.dumps(scenarios.to_dict(orient="records"), indent=2),
    }
    st.download_button(
        label="Download Presentation Report (.txt)",
        data=build_report(payload),
        file_name="crop_intelligence_report.txt",
        mime="text/plain",
        use_container_width=False,
    )

    if not data.empty:
        with st.expander("Dataset Snapshot"):
            st.dataframe(data.head(10), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
