# ============================================================
# main.py — AI-Powered Crop Yield Prediction & Optimization
# Purpose : Accept user inputs (console or GUI), load the
#           trained model, predict crop yield, and display
#           a detailed summary with a result chart.
# ============================================================

import os
import sys
import pickle
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec

# ── Try to import Tkinter (optional GUI) ──────────────────
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Base directory — keeps file paths clean
BASE = os.path.dirname(os.path.abspath(__file__))

# Crop-specific guidance profiles used for suitability scoring.
CROP_PROFILES = {
    "Rice": {
        "rainfall": (1200, 2000),
        "temperature": (22, 35),
        "soil_nutrients": (55, 100),
        "note": "Thrives in high rainfall and warm conditions.",
    },
    "Wheat": {
        "rainfall": (400, 900),
        "temperature": (12, 25),
        "soil_nutrients": (45, 85),
        "note": "Performs best in cooler to mild climates.",
    },
    "Maize": {
        "rainfall": (500, 1200),
        "temperature": (18, 32),
        "soil_nutrients": (40, 80),
        "note": "Good all-round crop for moderate environments.",
    },
    "Cotton": {
        "rainfall": (500, 1000),
        "temperature": (20, 35),
        "soil_nutrients": (45, 85),
        "note": "Needs warmth and balanced moisture.",
    },
    "Soybean": {
        "rainfall": (450, 1000),
        "temperature": (18, 30),
        "soil_nutrients": (50, 90),
        "note": "Suitable in warm regions with moderate rainfall.",
    },
    "Sugarcane": {
        "rainfall": (1000, 1800),
        "temperature": (20, 35),
        "soil_nutrients": (60, 100),
        "note": "High-yield crop under warm and moist conditions.",
    },
}


# ─────────────────────────────────────────────
# Helper — load the pre-trained model
# ─────────────────────────────────────────────
def load_model(filepath=None):
    """Load the pickled Random Forest model from disk."""
    if filepath is None:
        filepath = os.path.join(BASE, "crop_model.pkl")

    if not os.path.exists(filepath):
        print("❌  Model file not found!  Please run  model.py  first.\n")
        sys.exit(1)

    with open(filepath, "rb") as f:
        model = pickle.load(f)
    return model


# ─────────────────────────────────────────────
# Core — prediction logic
# ─────────────────────────────────────────────
def predict_yield(model, rainfall, temperature, soil_nutrients):
    """
    Run the model on the three input features and return
    the predicted yield in kg/ha.
    """
    features = pd.DataFrame(
        [[rainfall, temperature, soil_nutrients]],
        columns=["rainfall", "temperature", "soil_nutrients"]
    )
    predicted = model.predict(features)[0]
    return round(predicted, 2)


# ─────────────────────────────────────────────
# Helper — classify yield into a simple category
# ─────────────────────────────────────────────
def classify_yield(yield_value):
    """Return a human-readable yield category and advice string."""
    if yield_value < 2500:
        return "🔴 Low", "Consider improving irrigation and soil health."
    elif yield_value < 3500:
        return "🟡 Moderate", "Yield is average. Optimise soil nutrients for better results."
    elif yield_value < 4500:
        return "🟢 Good", "Good yield! Maintain current farming practices."
    else:
        return "🏆 Excellent", "Outstanding yield! Conditions are near optimal."


def _feature_score(value, low, high):
    """Return a score in [0, 1] based on closeness to an ideal range."""
    if low <= value <= high:
        return 1.0
    span = max(high - low, 1e-6)
    if value < low:
        return max(0.0, 1.0 - ((low - value) / span))
    return max(0.0, 1.0 - ((value - high) / span))


def analyze_crop_suitability(rainfall, temperature, soil_nutrients):
    """
    Score each crop profile against the input conditions.
    Returns list of dicts sorted by suitability (best first).
    """
    results = []
    for crop_name, profile in CROP_PROFILES.items():
        rain_score = _feature_score(rainfall, *profile["rainfall"])
        temp_score = _feature_score(temperature, *profile["temperature"])
        nutrient_score = _feature_score(soil_nutrients, *profile["soil_nutrients"])

        # Weighted to prioritise climate slightly over nutrients.
        suitability = (0.4 * rain_score) + (0.35 * temp_score) + (0.25 * nutrient_score)
        results.append(
            {
                "crop": crop_name,
                "suitability": round(suitability * 100, 1),
                "rain_score": rain_score,
                "temp_score": temp_score,
                "nutrient_score": nutrient_score,
                "note": profile["note"],
            }
        )

    results.sort(key=lambda x: x["suitability"], reverse=True)
    return results


def estimate_crop_yield_for_profile(base_yield, crop_result):
    """
    Adjust baseline model yield using crop suitability score.
    This is a heuristic layer, not an independent ML estimate.
    """
    suitability_factor = crop_result["suitability"] / 100.0
    adjusted = base_yield * (0.7 + 0.3 * suitability_factor)
    return round(adjusted, 2)


# ─────────────────────────────────────────────
# Visualisation — result dashboard chart
# ─────────────────────────────────────────────
def plot_prediction_result(rainfall, temperature, soil_nutrients, predicted_yield,
                           save_path=None, show=True):
    """
    Three-panel dashboard:
      Left  — Input parameter bar chart
      Right — Gauge-style yield result
    """
    fig = plt.figure(figsize=(12, 5))
    fig.patch.set_facecolor("#f0f4f0")
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    # ── Panel 1 : Input Parameters ───────────────────────
    ax1 = fig.add_subplot(gs[0])

    param_names  = ["Rainfall\n(mm)", "Temperature\n(°C)", "Soil Nutrients\n(index)"]
    param_values = [rainfall, temperature, soil_nutrients]
    param_max    = [2000, 40, 100]          # practical maxima for normalisation
    bar_colors   = ["#2196F3", "#FF9800", "#4CAF50"]

    bars = ax1.barh(param_names, param_values, color=bar_colors,
                    edgecolor="white", linewidth=1.2, height=0.5)

    for bar, val in zip(bars, param_values):
        ax1.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
                 f"{val}", va="center", ha="left", fontsize=12, fontweight="bold")

    ax1.set_xlabel("Input Value", fontsize=11)
    ax1.set_title("Your Input Parameters", fontsize=13, fontweight="bold", pad=10)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.set_facecolor("#f9fbf9")
    ax1.set_xlim(0, max(param_values) * 1.25)

    # ── Panel 2 : Yield Result ────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor("#f9fbf9")
    ax2.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax2.set_xticks([])
    ax2.set_yticks([])

    category, advice = classify_yield(predicted_yield)

    # Colour based on category
    if "Low" in category:
        result_color = "#e53935"
    elif "Moderate" in category:
        result_color = "#FB8C00"
    elif "Good" in category:
        result_color = "#43A047"
    else:
        result_color = "#1E88E5"

    ax2.text(0.5, 0.82, "Predicted Crop Yield",
             ha="center", va="center", fontsize=13,
             fontweight="bold", transform=ax2.transAxes, color="#333")

    ax2.text(0.5, 0.58, f"{predicted_yield:,.0f} kg/ha",
             ha="center", va="center", fontsize=32,
             fontweight="bold", transform=ax2.transAxes, color=result_color)

    ax2.text(0.5, 0.40, category,
             ha="center", va="center", fontsize=16,
             fontweight="bold", transform=ax2.transAxes, color=result_color)

    ax2.text(0.5, 0.22, advice,
             ha="center", va="center", fontsize=10,
             transform=ax2.transAxes, color="#555",
             wrap=True, style="italic")

    # Decorative rectangle around the yield number
    rect = mpatches.FancyBboxPatch(
        (0.08, 0.12), 0.84, 0.82,
        boxstyle="round,pad=0.02",
        linewidth=2, edgecolor=result_color,
        facecolor="white", transform=ax2.transAxes, zorder=0
    )
    ax2.add_patch(rect)

    ax2.set_title("Prediction Result", fontsize=13, fontweight="bold", pad=10)

    plt.suptitle("🌾  AI-Powered Crop Yield Prediction  🌾",
                 fontsize=15, fontweight="bold", y=1.02, color="#2e7d32")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"\n   📊 Result chart saved → {save_path}")
    if show:
        plt.show()
    plt.close()


# ─────────────────────────────────────────────
# Console — user input & prediction flow
# ─────────────────────────────────────────────
def run_console():
    """Prompt the user for inputs, predict yield, and show results."""
    print("\n" + "=" * 55)
    print("  🌾  AI-Powered Crop Yield Prediction & Optimization")
    print("=" * 55)
    print("  Enter the following field values to get a prediction.")
    print("  (Press Ctrl+C at any time to exit)\n")

    model = load_model()

    # ── Collect inputs with validation ─────────────────
    def get_float(prompt, low, high):
        while True:
            try:
                val = float(input(prompt))
                if low <= val <= high:
                    return val
                print(f"  ⚠️  Please enter a value between {low} and {high}.")
            except ValueError:
                print("  ⚠️  Invalid input — please enter a number.")

    rainfall        = get_float("  Rainfall (mm)         [0 – 2000]  : ", 0, 2000)
    temperature     = get_float("  Temperature (°C)      [0 – 50]    : ", 0, 50)
    soil_nutrients  = get_float("  Soil Nutrients (0–100)[0 – 100]   : ", 0, 100)

    # ── Predict ────────────────────────────────────────
    predicted = predict_yield(model, rainfall, temperature, soil_nutrients)
    category, advice = classify_yield(predicted)

    # ── Print summary report ───────────────────────────
    print("\n" + "─" * 55)
    print("  📋  PREDICTION SUMMARY REPORT")
    print("─" * 55)
    print(f"  Rainfall        : {rainfall} mm")
    print(f"  Temperature     : {temperature} °C")
    print(f"  Soil Nutrients  : {soil_nutrients} (index)")
    print("─" * 55)
    print(f"  🌱 Predicted Yield : {predicted:,.2f} kg/ha")
    print(f"  📊 Yield Category  : {category}")
    print(f"  💡 Suggestion      : {advice}")
    print("─" * 55)

    # ── Show / save result chart ───────────────────────
    chart_path = os.path.join(BASE, "prediction_result.png")
    plot_prediction_result(
        rainfall, temperature, soil_nutrients, predicted,
        save_path=chart_path, show=True
    )

    print("\n✅  Done!  Check  prediction_result.png  for the saved chart.")
    print("=" * 55 + "\n")


# ─────────────────────────────────────────────
# GUI — Tkinter interface (optional)
# ─────────────────────────────────────────────
def run_gui():
    """Launch a modern Tkinter GUI with crop comparison features."""
    model = load_model()

    root = tk.Tk()
    root.title("Crop Intelligence Studio")
    root.geometry("920x620")
    root.resizable(False, False)
    root.configure(bg="#f4f7f5")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame", background="#f4f7f5")
    style.configure("Card.TFrame", background="#ffffff", relief="flat")
    style.configure("Header.TLabel", background="#f4f7f5", foreground="#18221f",
                    font=("Segoe UI", 20, "bold"))
    style.configure("SubHeader.TLabel", background="#f4f7f5", foreground="#5f6d67",
                    font=("Segoe UI", 10))
    style.configure("Title.TLabel", background="#ffffff", foreground="#1f2a25",
                    font=("Segoe UI", 11, "bold"))
    style.configure("Body.TLabel", background="#ffffff", foreground="#4e5b55",
                    font=("Segoe UI", 10))
    style.configure("Accent.TButton", background="#0f6b46", foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=8)
    style.map("Accent.TButton", background=[("active", "#0c5b3b")])

    shell = ttk.Frame(root, padding=16)
    shell.pack(fill="both", expand=True)

    header = ttk.Frame(shell)
    header.pack(fill="x", pady=(0, 10))
    ttk.Label(header, text="Crop Intelligence Studio", style="Header.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text="Modern crop prediction with suitability analysis and multi-crop comparison",
        style="SubHeader.TLabel"
    ).pack(anchor="w")

    content = ttk.Frame(shell)
    content.pack(fill="both", expand=True)
    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    left_card = ttk.Frame(content, style="Card.TFrame", padding=16)
    left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    right_card = ttk.Frame(content, style="Card.TFrame", padding=16)
    right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    ttk.Label(left_card, text="Field Parameters", style="Title.TLabel").pack(anchor="w")

    fields = [("Rainfall (mm)", 0, 2000), ("Temperature (°C)", 0, 50), ("Soil Nutrients (0-100)", 0, 100)]
    entries = {}
    for label, lo, hi in fields:
        row = ttk.Frame(left_card, style="Card.TFrame")
        row.pack(fill="x", pady=7)
        ttk.Label(row, text=label, style="Body.TLabel", width=22).pack(side="left")
        entry = ttk.Entry(row, width=14)
        entry.pack(side="left", padx=(6, 0))
        entries[label] = (entry, lo, hi)

    crop_row = ttk.Frame(left_card, style="Card.TFrame")
    crop_row.pack(fill="x", pady=(4, 10))
    ttk.Label(crop_row, text="Focus Crop", style="Body.TLabel", width=22).pack(side="left")
    crop_choice = ttk.Combobox(crop_row, state="readonly", width=16, values=list(CROP_PROFILES.keys()))
    crop_choice.set("Rice")
    crop_choice.pack(side="left", padx=(6, 0))

    result_var = tk.StringVar(value="Enter values and click Predict to see yield insights.")
    ttk.Label(left_card, textvariable=result_var, style="Body.TLabel", wraplength=380, justify="left").pack(
        anchor="w", pady=(8, 4)
    )

    advice_var = tk.StringVar(value="")
    ttk.Label(left_card, textvariable=advice_var, style="Body.TLabel", wraplength=380, justify="left").pack(
        anchor="w", pady=(0, 10)
    )

    ttk.Label(right_card, text="Crop Comparison", style="Title.TLabel").pack(anchor="w")
    columns = ("crop", "suitability", "yield", "note")
    table = ttk.Treeview(right_card, columns=columns, show="headings", height=16)
    table.heading("crop", text="Crop")
    table.heading("suitability", text="Suitability")
    table.heading("yield", text="Estimated Yield")
    table.heading("note", text="Condition Fit")
    table.column("crop", width=100, anchor="w")
    table.column("suitability", width=100, anchor="center")
    table.column("yield", width=120, anchor="center")
    table.column("note", width=220, anchor="w")
    table.pack(fill="both", expand=True, pady=(8, 0))

    def on_predict():
        vals = {}
        for label, (entry, lo, hi) in entries.items():
            raw = entry.get().strip()
            try:
                v = float(raw)
                if not (lo <= v <= hi):
                    messagebox.showerror(
                        "Out of Range",
                        f"{label} must be between {lo} and {hi}."
                    )
                    return
                vals[label] = round(v, 2)
            except ValueError:
                messagebox.showerror("Invalid Input", f"Please enter a number for {label}.")
                return

        rainfall_v    = vals["Rainfall (mm)"]
        temperature_v = vals["Temperature (°C)"]
        nutrients_v   = vals["Soil Nutrients (0-100)"]

        predicted     = predict_yield(model, rainfall_v, temperature_v, nutrients_v)
        category, tip = classify_yield(predicted)
        ranked_crops = analyze_crop_suitability(rainfall_v, temperature_v, nutrients_v)
        selected_crop = crop_choice.get()
        selected_info = next(item for item in ranked_crops if item["crop"] == selected_crop)
        selected_estimated_yield = estimate_crop_yield_for_profile(predicted, selected_info)

        result_var.set(
            f"Base predicted yield: {predicted:,.2f} kg/ha ({category})\n"
            f"{selected_crop} suitability: {selected_info['suitability']:.1f}%  |  "
            f"Estimated {selected_crop} yield: {selected_estimated_yield:,.2f} kg/ha"
        )
        advice_var.set(f"Insight: {selected_info['note']}  |  Tip: {tip}")

        for item_id in table.get_children():
            table.delete(item_id)
        for crop_result in ranked_crops:
            est_yield = estimate_crop_yield_for_profile(predicted, crop_result)
            table.insert(
                "",
                "end",
                values=(
                    crop_result["crop"],
                    f"{crop_result['suitability']:.1f}%",
                    f"{est_yield:,.0f} kg/ha",
                    crop_result["note"],
                ),
            )

        chart_path = os.path.join(BASE, "prediction_result.png")
        plot_prediction_result(
            rainfall_v, temperature_v, nutrients_v, predicted,
            save_path=chart_path, show=True
        )

    action_row = ttk.Frame(left_card, style="Card.TFrame")
    action_row.pack(fill="x", pady=(2, 0))
    ttk.Button(action_row, text="Predict & Compare Crops", style="Accent.TButton", command=on_predict).pack(
        side="left"
    )

    root.mainloop()


# ─────────────────────────────────────────────
# Entry point — auto-select GUI or console
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Check for --console flag to force terminal mode
    if "--console" in sys.argv:
        run_console()
    elif TKINTER_AVAILABLE:
        print("Launching Tkinter GUI... (use --console for terminal mode)")
        run_gui()
    else:
        print("Tkinter not available - falling back to console mode.\n")
        run_console()
