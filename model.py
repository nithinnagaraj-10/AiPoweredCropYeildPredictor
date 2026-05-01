# ============================================================
# model.py — AI-Powered Crop Yield Prediction & Optimization
# Purpose : Load data, train a Random Forest model, evaluate
#           it, and save it so main.py can load it later.
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

# ─────────────────────────────────────────────
# STEP 1 — Load the dataset
# ─────────────────────────────────────────────
def load_data(filepath="data.csv"):
    """Read the CSV dataset and return a DataFrame."""
    df = pd.read_csv(filepath)
    print("✅ Dataset loaded successfully!")
    print(f"   Shape : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"   Columns: {list(df.columns)}\n")
    return df


# ─────────────────────────────────────────────
# STEP 2 — Train the model
# ─────────────────────────────────────────────
def train_model(df):
    """
    Split data into features (X) and target (y),
    train a Random Forest Regressor, and return
    the trained model together with test data.
    """
    # Features → inputs  |  Target → what we predict
    X = df[["rainfall", "temperature", "soil_nutrients"]]
    y = df["yield"]

    # 80 % train, 20 % test  (random_state keeps it reproducible)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Random Forest — an ensemble of decision trees
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("✅ Model trained successfully!\n")
    return model, X_test, y_test


# ─────────────────────────────────────────────
# STEP 3 — Evaluate the model
# ─────────────────────────────────────────────
def evaluate_model(model, X_test, y_test):
    """Print MAE and R² score on the held-out test set."""
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    print("📊 Model Evaluation")
    print("=" * 35)
    print(f"   Mean Absolute Error : {mae:.2f} kg/ha")
    print(f"   R² Score            : {r2:.4f}  ({r2*100:.1f}% variance explained)")
    print("=" * 35)
    print()
    return y_pred


# ─────────────────────────────────────────────
# STEP 4 — Visualisations
# ─────────────────────────────────────────────
def plot_feature_importance(model, save_path="feature_importance.png"):
    """Bar chart of feature importances from the Random Forest."""
    features    = ["Rainfall", "Temperature", "Soil Nutrients"]
    importances = model.feature_importances_

    colors = ["#4CAF50", "#FF9800", "#2196F3"]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(features, importances, color=colors, edgecolor="white", linewidth=1.2)

    # Label each bar
    for bar, val in zip(bars, importances):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.005,
            f"{val:.3f}",
            ha="center", va="bottom", fontsize=11, fontweight="bold"
        )

    ax.set_title("Feature Importance — Random Forest", fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Importance Score", fontsize=11)
    ax.set_ylim(0, max(importances) + 0.1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"   📈 Feature importance chart saved → {save_path}")


def plot_actual_vs_predicted(y_test, y_pred, save_path="actual_vs_predicted.png"):
    """Scatter plot of actual vs predicted yield values."""
    fig, ax = plt.subplots(figsize=(6, 5))

    ax.scatter(y_test, y_pred, color="#4CAF50", edgecolors="white",
               linewidth=0.8, s=80, alpha=0.85, label="Predictions")

    # Perfect prediction line
    min_val = min(min(y_test), min(y_pred)) - 100
    max_val = max(max(y_test), max(y_pred)) + 100
    ax.plot([min_val, max_val], [min_val, max_val],
            "r--", linewidth=1.5, label="Perfect Fit")

    ax.set_xlabel("Actual Yield (kg/ha)", fontsize=11)
    ax.set_ylabel("Predicted Yield (kg/ha)", fontsize=11)
    ax.set_title("Actual vs Predicted Crop Yield", fontsize=14, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_facecolor("#f9f9f9")
    fig.patch.set_facecolor("white")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"   📈 Actual vs Predicted chart saved  → {save_path}")


def plot_dataset_overview(df, save_path="dataset_overview.png"):
    """3-panel chart showing how each feature correlates with yield."""
    features = ["rainfall", "temperature", "soil_nutrients"]
    labels   = ["Rainfall (mm)", "Temperature (°C)", "Soil Nutrients (index)"]
    colors   = ["#2196F3", "#FF9800", "#4CAF50"]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle("Feature vs Crop Yield", fontsize=15, fontweight="bold", y=1.02)

    for ax, feat, label, color in zip(axes, features, labels, colors):
        ax.scatter(df[feat], df["yield"], color=color,
                   edgecolors="white", linewidth=0.6, s=55, alpha=0.8)
        # Trend line
        z = np.polyfit(df[feat], df["yield"], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df[feat].min(), df[feat].max(), 100)
        ax.plot(x_line, p(x_line), "r--", linewidth=1.4, label="Trend")

        ax.set_xlabel(label, fontsize=10)
        ax.set_ylabel("Yield (kg/ha)", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_facecolor("#f9f9f9")
        ax.legend(fontsize=9)

    fig.patch.set_facecolor("white")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"   📈 Dataset overview chart saved     → {save_path}")


# ─────────────────────────────────────────────
# STEP 5 — Save the trained model
# ─────────────────────────────────────────────
def save_model(model, filepath="crop_model.pkl"):
    """Serialise the model to disk with pickle."""
    with open(filepath, "wb") as f:
        pickle.dump(model, f)
    print(f"\n✅ Model saved → {filepath}")


# ─────────────────────────────────────────────
# MAIN — run training pipeline
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  🌾 Crop Yield Prediction — Model Training")
    print("=" * 50 + "\n")

    # Resolve paths so the script works from any directory
    base = os.path.dirname(os.path.abspath(__file__))

    df               = load_data(os.path.join(base, "data.csv"))
    model, X_t, y_t  = train_model(df)
    y_pred           = evaluate_model(model, X_t, y_t)

    print("📉 Generating visualisation charts …")
    plot_feature_importance(model, os.path.join(base, "feature_importance.png"))
    plot_actual_vs_predicted(y_t, y_pred, os.path.join(base, "actual_vs_predicted.png"))
    plot_dataset_overview(df,            os.path.join(base, "dataset_overview.png"))

    save_model(model, os.path.join(base, "crop_model.pkl"))

    print("\n🎉 Training complete!  Run  main.py  to make predictions.\n")
