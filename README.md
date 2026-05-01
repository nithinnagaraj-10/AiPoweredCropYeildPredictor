# 🌾 AI-Powered Crop Yield Prediction & Optimization

A beginner-friendly Python mini-project that uses a **Random Forest** machine
learning model to predict crop yield (kg/ha) from three agronomic inputs:
Rainfall, Temperature, and Soil Nutrients.

---

## 📂 Project Structure

```
crop_yield_project/
├── data.csv              ← Sample dataset (35 records)
├── model.py              ← Training pipeline + evaluation + charts
├── main.py               ← Prediction app (GUI + console)
└── README.md             ← This file

Generated after running model.py:
├── crop_model.pkl        ← Saved Random Forest model
├── feature_importance.png
├── actual_vs_predicted.png
└── dataset_overview.png

Generated after each prediction:
└── prediction_result.png
```

---

## 🚀 How to Run

### 1 — Install dependencies
```bash
pip install pandas numpy scikit-learn matplotlib
```

### 2 — Train the model
```bash
python model.py
```
This will:
- Load `data.csv`
- Train a Random Forest Regressor (80/20 split)
- Print MAE and R² evaluation scores
- Save three visualisation charts (PNG)
- Save `crop_model.pkl`

### 3 — Run the prediction app

**With Tkinter GUI (default if Tkinter is installed):**
```bash
python main.py
```

**Console / terminal mode:**
```bash
python main.py --console
```

**Modern web dashboard (recommended for presentation):**
```bash
pip install streamlit plotly
streamlit run app.py
```

---

## 📊 Model Details

| Property      | Value                       |
|---------------|-----------------------------|
| Algorithm     | Random Forest Regressor     |
| Trees         | 100 estimators              |
| Train / Test  | 80 % / 20 %                 |
| Metric        | MAE, R² Score               |

---

## 🖼️ Output Charts

| File                        | Contents                               |
|-----------------------------|----------------------------------------|
| `feature_importance.png`    | Which inputs matter most               |
| `actual_vs_predicted.png`   | Model accuracy on test data            |
| `dataset_overview.png`      | Feature vs Yield scatter with trendline|
| `prediction_result.png`     | Dashboard for the latest prediction    |

---

## 💡 Yield Categories

| Yield (kg/ha)  | Category  |
|----------------|-----------|
| < 2 500        | 🔴 Low    |
| 2 500 – 3 499  | 🟡 Moderate|
| 3 500 – 4 499  | 🟢 Good   |
| ≥ 4 500        | 🏆 Excellent|

---

## 📚 Libraries Used

- **Pandas** — data loading & manipulation
- **NumPy** — numerical operations
- **Scikit-learn** — Random Forest model, metrics, train/test split
- **Matplotlib** — data visualisation
- **Tkinter** — optional GUI (bundled with standard Python)
