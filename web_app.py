import os
import pickle
import pandas as pd
from flask import Flask, render_template, request, jsonify
import sqlite3
import uuid
import json
import requests
import socket

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "crop_model.pkl")
DB_PATH = os.path.join(BASE, "reports.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (id TEXT PRIMARY KEY, farmer_name TEXT, contact TEXT, data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Load the model
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

model = load_model()

CROP_PROFILES = {
    # Cereals & Millets
    "Rice": {"rainfall": (1200, 2000), "temperature": (22, 35), "soil_nutrients": (55, 100), "note": "Kharif staple. Thrives in high rainfall and warm conditions."},
    "Wheat": {"rainfall": (400, 900), "temperature": (12, 25), "soil_nutrients": (45, 85), "note": "Rabi staple. Performs best in cooler to mild winter climates."},
    "Maize": {"rainfall": (500, 1000), "temperature": (18, 32), "soil_nutrients": (40, 80), "note": "Adaptive crop suitable for both Kharif and Rabi in some regions."},
    "Jowar (Sorghum)": {"rainfall": (300, 600), "temperature": (26, 33), "soil_nutrients": (30, 70), "note": "Hardy millet. Highly drought-resistant and heat tolerant."},
    "Bajra (Pearl Millet)": {"rainfall": (250, 500), "temperature": (25, 35), "soil_nutrients": (20, 60), "note": "Excellent for arid regions with poor soil."},
    "Ragi (Finger Millet)": {"rainfall": (500, 1000), "temperature": (20, 30), "soil_nutrients": (30, 70), "note": "Highly nutritious, thrives in moderately dry to wet conditions."},
    
    # Pulses & Beans
    "Gram (Chickpea)": {"rainfall": (400, 600), "temperature": (20, 30), "soil_nutrients": (40, 70), "note": "Major Rabi pulse. Needs minimal water."},
    "Tur / Arhar (Pigeon Pea)": {"rainfall": (600, 1000), "temperature": (25, 35), "soil_nutrients": (45, 75), "note": "Deep-rooted Kharif pulse. Survives dry spells well."},
    "Moong (Green Gram)": {"rainfall": (400, 600), "temperature": (25, 35), "soil_nutrients": (35, 65), "note": "Short duration Zaid/Kharif crop."},
    "Urad (Black Gram)": {"rainfall": (400, 600), "temperature": (25, 35), "soil_nutrients": (35, 65), "note": "Warm weather pulse. Excellent for crop rotation."},
    "Soybean": {"rainfall": (600, 1000), "temperature": (20, 30), "soil_nutrients": (50, 90), "note": "Kharif commercial pulse. Requires good soil moisture."},
    "Rajma (Kidney Beans)": {"rainfall": (600, 1500), "temperature": (15, 25), "soil_nutrients": (50, 80), "note": "Grown in mild climates or hilly regions."},

    # Cash & Commercial Crops
    "Cotton": {"rainfall": (500, 1000), "temperature": (21, 35), "soil_nutrients": (45, 85), "note": "Needs warmth, balanced moisture, and clear skies for harvesting."},
    "Sugarcane": {"rainfall": (1500, 2500), "temperature": (20, 35), "soil_nutrients": (60, 100), "note": "Long-duration crop. High-yield under warm and moist conditions."},
    "Jute": {"rainfall": (1500, 2000), "temperature": (24, 38), "soil_nutrients": (60, 90), "note": "Hot and humid climate required. Major cash crop in eastern India."},
    "Tobacco": {"rainfall": (500, 800), "temperature": (20, 30), "soil_nutrients": (50, 85), "note": "Requires frost-free climate and well-drained soil."},
    "Mustard (Oilseed)": {"rainfall": (300, 500), "temperature": (10, 25), "soil_nutrients": (40, 75), "note": "Rabi oilseed crop. Frost sensitive."},
    "Groundnut": {"rainfall": (500, 1000), "temperature": (25, 35), "soil_nutrients": (40, 80), "note": "Requires loose, well-drained soil for pod formation."},
    "Sunflower": {"rainfall": (300, 600), "temperature": (20, 30), "soil_nutrients": (40, 80), "note": "Photo-insensitive crop, can be grown year-round in mild climates."},

    # Spices & Plantation
    "Tea": {"rainfall": (1500, 3000), "temperature": (15, 30), "soil_nutrients": (60, 95), "note": "Requires evenly distributed high rainfall and acidic soil."},
    "Coffee": {"rainfall": (1500, 2500), "temperature": (15, 28), "soil_nutrients": (55, 90), "note": "Needs hot and humid climate with dry spells for ripening."},
    "Turmeric": {"rainfall": (1000, 2000), "temperature": (20, 30), "soil_nutrients": (60, 90), "note": "Highly profitable spice. Requires rich loamy soil."},
    "Ginger": {"rainfall": (1500, 2500), "temperature": (25, 35), "soil_nutrients": (65, 95), "note": "Needs high humidity and warm climate."},
    "Garlic": {"rainfall": (400, 700), "temperature": (12, 25), "soil_nutrients": (50, 85), "note": "Cool season crop, needs well-drained soil."},
    "Chilli": {"rainfall": (600, 1200), "temperature": (20, 30), "soil_nutrients": (45, 80), "note": "Requires warm and humid climate."},
    "Coriander": {"rainfall": (300, 500), "temperature": (15, 25), "soil_nutrients": (40, 75), "note": "Dry and cool weather is best for seed formation."},

    # Fruits, Vegetables & Exotic
    "Potato": {"rainfall": (300, 500), "temperature": (15, 25), "soil_nutrients": (50, 90), "note": "Cool season tuber. Sandy loam soil preferred."},
    "Onion": {"rainfall": (500, 750), "temperature": (15, 25), "soil_nutrients": (45, 80), "note": "Requires cool phase for vegetative growth, warm for bulb maturity."},
    "Tomato": {"rainfall": (400, 600), "temperature": (20, 28), "soil_nutrients": (50, 85), "note": "Warm season crop. Cannot tolerate frost."},
    "Brinjal (Eggplant)": {"rainfall": (500, 800), "temperature": (22, 30), "soil_nutrients": (45, 80), "note": "Hardy vegetable. Needs long warm growing season."},
    "Cabbage": {"rainfall": (300, 500), "temperature": (15, 20), "soil_nutrients": (55, 85), "note": "Cool season crop. Requires continuous moisture."},
    "Cauliflower": {"rainfall": (300, 500), "temperature": (15, 20), "soil_nutrients": (55, 85), "note": "Sensitive to weather fluctuations."},
    "Okra (Bhindi)": {"rainfall": (500, 1000), "temperature": (22, 35), "soil_nutrients": (40, 75), "note": "Thrives in hot and humid conditions."},
    "Spinach (Palak)": {"rainfall": (300, 500), "temperature": (10, 22), "soil_nutrients": (50, 85), "note": "Cool season leafy green. Needs nitrogen-rich soil."},
    "Bottle Gourd": {"rainfall": (500, 800), "temperature": (25, 35), "soil_nutrients": (40, 75), "note": "Warm season vine. Needs good drainage."},
    "Bitter Gourd": {"rainfall": (500, 800), "temperature": (25, 35), "soil_nutrients": (40, 75), "note": "Warm season vine. High medicinal value."},
    "Carrot": {"rainfall": (300, 500), "temperature": (10, 20), "soil_nutrients": (45, 80), "note": "Cool season root. Loose soil required for straight roots."},
    "Radish": {"rainfall": (300, 500), "temperature": (10, 20), "soil_nutrients": (45, 80), "note": "Fast-growing cool season root crop."},
    "Mango": {"rainfall": (1000, 2500), "temperature": (24, 30), "soil_nutrients": (50, 90), "note": "King of fruits. Needs dry period before flowering."},
    "Banana": {"rainfall": (1500, 2500), "temperature": (20, 30), "soil_nutrients": (60, 100), "note": "High water and nutrient requirement year-round."},
    "Papaya": {"rainfall": (1000, 1500), "temperature": (25, 35), "soil_nutrients": (50, 90), "note": "Fast-growing fruit. Highly sensitive to waterlogging."},
    "Dragon Fruit": {"rainfall": (500, 1000), "temperature": (20, 30), "soil_nutrients": (30, 70), "note": "Exotic cactus crop. Very low water requirement."},
    "Quinoa": {"rainfall": (300, 500), "temperature": (10, 25), "soil_nutrients": (30, 70), "note": "Exotic superfood. Extremely hardy and drought-resistant."},
    "Chia Seeds": {"rainfall": (400, 800), "temperature": (15, 30), "soil_nutrients": (35, 75), "note": "Exotic health crop. Needs well-drained soil and warmth."}
}

def predict_yield_val(rainfall, temperature, soil_nutrients):
    if not model:
        return 0.0
    features = pd.DataFrame(
        [[rainfall, temperature, soil_nutrients]],
        columns=["rainfall", "temperature", "soil_nutrients"]
    )
    return round(model.predict(features)[0], 2)

def classify_yield(yield_value):
    if yield_value < 2500:
        return "Low", "Consider improving irrigation and soil health."
    elif yield_value < 3500:
        return "Moderate", "Yield is average. Optimise soil nutrients for better results."
    elif yield_value < 4500:
        return "Good", "Good yield! Maintain current farming practices."
    else:
        return "Excellent", "Outstanding yield! Conditions are near optimal."

def _feature_score(value, low, high):
    if low <= value <= high:
        return 1.0
    span = max(high - low, 1e-6)
    if value < low:
        return max(0.0, 1.0 - ((low - value) / span))
    return max(0.0, 1.0 - ((value - high) / span))

def analyze_crop_suitability(rainfall, temperature, soil_nutrients):
    results = []
    for crop_name, profile in CROP_PROFILES.items():
        rain_score = _feature_score(rainfall, *profile["rainfall"])
        temp_score = _feature_score(temperature, *profile["temperature"])
        nutrient_score = _feature_score(soil_nutrients, *profile["soil_nutrients"])

        suitability = (0.4 * rain_score) + (0.35 * temp_score) + (0.25 * nutrient_score)
        results.append(
            {
                "crop": crop_name,
                "suitability": round(suitability * 100, 1),
                "note": profile["note"],
            }
        )
    results.sort(key=lambda x: x["suitability"], reverse=True)
    return results

def estimate_crop_yield_for_profile(base_yield, crop_result):
    suitability_factor = crop_result["suitability"] / 100.0
    adjusted = base_yield * (0.7 + 0.3 * suitability_factor)
    return round(adjusted, 2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json
    try:
        def safe_float(val, default=0.0):
            try: return float(val) if val != "" else default
            except (ValueError, TypeError): return default

        rainfall = safe_float(data.get("rainfall", 0))
        temperature = safe_float(data.get("temperature", 0))
        soil_nutrients = safe_float(data.get("soil_nutrients", 0))
        focus_crop = data.get("focus_crop", "Rice")
        
        base_yield = predict_yield_val(rainfall, temperature, soil_nutrients)
        category, advice = classify_yield(base_yield)
        
        ranked_crops = analyze_crop_suitability(rainfall, temperature, soil_nutrients)
        focused_info = next((c for c in ranked_crops if c["crop"] == focus_crop), ranked_crops[0])
        est_focus_yield = estimate_crop_yield_for_profile(base_yield, focused_info)
        
        # Scenarios
        dry_yield = predict_yield_val(max(rainfall - 250, 0), temperature + 1.5, max(soil_nutrients - 5, 0))
        optimal_yield = predict_yield_val(rainfall + 150, max(temperature - 1.0, 0), min(soil_nutrients + 10, 100))
        
        response = {
            "success": True,
            "base_yield": base_yield,
            "category": category,
            "advice": advice,
            "focus_crop": focus_crop,
            "focus_suitability": focused_info["suitability"],
            "focus_est_yield": est_focus_yield,
            "focus_note": focused_info["note"],
            "all_crops": [{
                 "crop": c["crop"], 
                 "suitability": c["suitability"], 
                 "est_yield": estimate_crop_yield_for_profile(base_yield, c),
                 "note": c["note"]
            } for c in ranked_crops],
            "scenarios": {
                "dry_spell": dry_yield,
                "optimal_plan": optimal_yield
            }
        }
    except Exception as e:
        response = {"success": False, "error": str(e)}
        
    return jsonify(response)

@app.route("/api/weather", methods=["POST"])
def api_weather():
    data = request.json
    pincode = str(data.get("pincode", ""))
    
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return jsonify({"success": False, "error": "Invalid Indian Pincode. Must be 6 digits."})
        
    try:
        # 1. Geocode pincode to get lat/lon
        geo_url = f"https://nominatim.openstreetmap.org/search?postalcode={pincode}&country=india&format=json"
        geo_resp = requests.get(geo_url, headers={'User-Agent': 'AgriPredict/1.0'})
        geo_data = geo_resp.json()
        
        if not geo_data:
            return jsonify({"success": False, "error": "Could not find coordinates for this pincode."})
            
        lat = float(geo_data[0]['lat'])
        lon = float(geo_data[0]['lon'])
        region = geo_data[0].get('display_name', '').split(',')[0]
        
        # 2. Generate Seasonal Averages based on Lat/Lon Geography
        # Temp baseline (approximate summer max): cooler as you go North
        base_temp = 38 - (lat - 8) * 0.4 
        
        # Rain baseline (Annual mm)
        if lon > 85: base_rain = 2200 # East/Northeast (High rain)
        elif lon < 75: base_rain = 600 # West/Rajasthan (Low rain)
        elif lat < 20: base_rain = 1500 # South/Coastal
        else: base_rain = 1100 # Central/North
        
        seasons = {
            "Monsoon": {
                "temp": round(base_temp - 6, 1),
                "rain": round(base_rain * 0.7) # 70% of annual rain
            },
            "Winter": {
                "temp": round(base_temp - 15 if lat > 24 else base_temp - 7, 1),
                "rain": round(base_rain * 0.05)
            },
            "Summer": {
                "temp": round(base_temp, 1),
                "rain": round(base_rain * 0.1)
            },
            "Spring": {
                "temp": round(base_temp - 4, 1),
                "rain": round(base_rain * 0.15)
            }
        }
        
        return jsonify({
            "success": True,
            "region": f"{region}",
            "seasons": seasons
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Weather API error: {e}"})

@app.route("/api/save_report", methods=["POST"])
def save_report():
    data = request.json
    report_id = str(uuid.uuid4())
    farmer_name = data.get("farmer_name", "Unknown")
    contact = data.get("contact", "Unknown")
    address = data.get("address", "Unknown")
    report_data = data.get("report_data", {})
    report_data["address"] = address  # Store address in JSON blob
    report_data_str = json.dumps(report_data)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO reports (id, farmer_name, contact, data) VALUES (?, ?, ?, ?)",
                  (report_id, farmer_name, contact, report_data_str))
        conn.commit()
        conn.close()
        
        # Get Local IP to ensure QR code is scannable from other devices
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()
            
        url = f"/report/{report_id}"
        full_url = f"http://{local_ip}:8000{url}"
        
        # Send Real SMS via Textbelt Free Tier (1 per day per IP)
        sms_sent = False
        if contact and contact != "Unknown" and contact != "Not Provided":
            try:
                # Basic formatting: ensure it looks like a phone number
                phone = ''.join(filter(str.isdigit, contact))
                if len(phone) >= 10:
                    resp = requests.post('https://textbelt.com/text', {
                        'phone': phone,
                        'message': f'AgriPredict: Hello {farmer_name}, your AI yield report is ready! View it here: {full_url}',
                        'key': 'textbelt',
                    })
                    resp_data = resp.json()
                    sms_sent = resp_data.get('success', False)
                    print(f"Textbelt API response: {resp_data}")
            except Exception as e:
                print(f"SMS Sending failed: {e}")
        
        return jsonify({"success": True, "report_id": report_id, "url": url, "full_url": full_url, "sms_sent": sms_sent})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT data, created_at FROM reports ORDER BY created_at DESC LIMIT 10")
        rows = c.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            data_str, created_at = row
            data = json.loads(data_str)
            
            try:
                from datetime import datetime
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                date_formatted = dt.strftime("%d %b, %H:%M")
            except:
                date_formatted = str(created_at).split('.')[0]
                
            history.append({
                "crop": data.get("focus_crop", "Unknown"),
                "category": data.get("category", ""),
                "rain": data.get("rainfall", 0),
                "temp": data.get("temperature", 0),
                "soil": data.get("soil_nutrients", 0),
                "date": date_formatted
            })
            
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/report/<report_id>")
def view_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT farmer_name, contact, data, created_at FROM reports WHERE id=?", (report_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return "Report not found", 404
        
    farmer_name, contact, data_str, created_at = row
    report_data = json.loads(data_str)
    
    return render_template("report_view.html", 
                           report_id=report_id,
                           farmer_name=farmer_name, 
                           contact=contact, 
                           data=report_data, 
                           created_at=created_at)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)
