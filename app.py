import os
import sqlite3
import json
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, g
)
import numpy as np
import pandas as pd
import joblib

app = Flask(__name__)
app.secret_key = "safezone_sih2026_ndrf_secret_key_prototype"
DATABASE = os.path.join(app.root_path, "database", "safezone.db")
MODEL_PATH = os.path.join(app.root_path, "model", "risk_model.pkl")
METADATA_PATH = os.path.join(app.root_path, "model", "risk_metadata.json")

# ==========================================
# DATABASE HELPERS
# ==========================================

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

# ==========================================
# DATABASE INITIALIZATION & SEEDING
# ==========================================

def init_db():
    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "model"), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Habitations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            state TEXT NOT NULL,
            population INTEGER NOT NULL,
            vulnerable_population INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            primary_hazard TEXT NOT NULL,
            elevation INTEGER NOT NULL,
            road_accessibility INTEGER NOT NULL,
            nearest_hospital_km REAL NOT NULL,
            nearest_school_km REAL NOT NULL,
            current_risk_score INTEGER NOT NULL,
            risk_category TEXT NOT NULL,
            relocation_status TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Hazards Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hazards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_id INTEGER NOT NULL,
            hazard_type TEXT NOT NULL,
            severity_level TEXT NOT NULL,
            rainfall_exposure INTEGER NOT NULL,
            slope_degrees INTEGER NOT NULL,
            historical_frequency INTEGER NOT NULL,
            distance_from_hazard_km REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habitation_id) REFERENCES habitations (id)
        )
    ''')
    
    # 4. Risk Assessments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_id INTEGER NOT NULL,
            hazard_exposure INTEGER NOT NULL,
            population_vulnerability INTEGER NOT NULL,
            historical_frequency INTEGER NOT NULL,
            infrastructure_vulnerability INTEGER NOT NULL,
            accessibility_risk INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_category TEXT NOT NULL,
            priority TEXT NOT NULL,
            assessed_by TEXT NOT NULL,
            date_assessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habitation_id) REFERENCES habitations (id)
        )
    ''')
    
    # 5. Safe Zones Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS safe_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            location_name TEXT NOT NULL,
            district TEXT NOT NULL,
            area_sqm INTEGER NOT NULL,
            estimated_capacity INTEGER NOT NULL,
            current_occupancy INTEGER NOT NULL,
            road_accessibility INTEGER NOT NULL,
            nearest_hospital_km REAL NOT NULL,
            nearest_school_km REAL NOT NULL,
            water_availability INTEGER NOT NULL,
            power_availability INTEGER NOT NULL,
            hazard_exposure INTEGER NOT NULL,
            suitability_score INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
    ''')
    
    # 6. Relocation Plans Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relocation_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_id INTEGER NOT NULL,
            safe_zone_id INTEGER NOT NULL,
            population_to_relocate INTEGER NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL,
            distance_km REAL NOT NULL,
            suitability_score INTEGER NOT NULL,
            recommended_action TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habitation_id) REFERENCES habitations (id),
            FOREIGN KEY (safe_zone_id) REFERENCES safe_zones (id)
        )
    ''')
    
    # 7. Alerts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'New',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (habitation_id) REFERENCES habitations (id)
        )
    ''')
    
    # 8. Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habitation_id INTEGER,
            inputs_json TEXT NOT NULL,
            risk_category TEXT NOT NULL,
            confidence REAL NOT NULL,
            risk_score INTEGER NOT NULL,
            priority TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    
    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_sample_data(cursor)
        conn.commit()
        
    conn.close()

def seed_sample_data(cursor):
    # Default Admin User
    cursor.execute(
        "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
        ("admin", "admin123", "Disaster Response Admin", "Administrator")
    )
    
    # Sample Habitations (15 realistic simulated settlements)
    habitations = [
        ("HAB-001", "Hillview Hamlet", "Mandi", "Himachal Pradesh", 420, 160, 31.7084, 76.9318, "Landslide", 1450, 25, 14.2, 8.5, 78, "CRITICAL", "Relocation Required"),
        ("HAB-002", "Riverbank Colony", "Wayanad", "Kerala", 680, 290, 11.6854, 76.1320, "Flood", 720, 35, 18.5, 6.2, 84, "CRITICAL", "Relocation Required"),
        ("HAB-003", "Kaveri Settlement", "Chamoli", "Uttarakhand", 310, 115, 30.4124, 79.3242, "Cloudburst", 1820, 20, 22.0, 11.0, 66, "HIGH", "Under Evaluation"),
        ("HAB-004", "Meadow Colony", "Uttarkashi", "Uttarakhand", 510, 195, 30.7268, 78.4432, "Extreme Rainfall", 1580, 40, 12.8, 5.4, 62, "HIGH", "Under Evaluation"),
        ("HAB-005", "North Slope Village", "Shimla", "Himachal Pradesh", 290, 98, 31.1048, 77.1734, "Landslide", 2100, 30, 15.0, 7.8, 58, "HIGH", "Monitoring"),
        ("HAB-006", "Coastal Reach", "Kendrapara", "Odisha", 850, 380, 20.5000, 86.4200, "Coastal Erosion", 15, 45, 9.5, 4.2, 72, "CRITICAL", "Relocation Required"),
        ("HAB-007", "Highland Settlement", "Tehri Garhwal", "Uttarakhand", 440, 140, 30.3800, 78.4800, "Multi-Hazard", 1650, 55, 11.2, 5.0, 44, "MODERATE", "Monitoring"),
        ("HAB-008", "Green Valley Hamlet", "Kullu", "Himachal Pradesh", 620, 180, 31.9579, 77.1095, "Flood", 1230, 65, 8.4, 3.8, 38, "MODERATE", "Safe"),
        ("HAB-009", "East Ridge Colony", "Darjeeling", "West Bengal", 390, 145, 27.0410, 88.2663, "Landslide", 2040, 35, 13.6, 6.9, 54, "HIGH", "Under Evaluation"),
        ("HAB-010", "Valley Point Settlement", "Rudraprayag", "Uttarakhand", 490, 210, 30.2844, 78.9811, "Cloudburst", 1390, 15, 19.4, 9.8, 76, "CRITICAL", "Relocation Required"),
        ("HAB-011", "South Creek Village", "Pathanamthitta", "Kerala", 560, 190, 9.2648, 76.7870, "Flood", 35, 60, 7.2, 3.5, 48, "MODERATE", "Monitoring"),
        ("HAB-012", "Western Slope", "Nilgiris", "Tamil Nadu", 270, 70, 11.4102, 76.6950, "Landslide", 1950, 80, 5.1, 2.8, 24, "LOW", "Safe"),
        ("HAB-013", "Lake Edge Colony", "Alappuzha", "Kerala", 720, 260, 9.4981, 76.3388, "Flood", 8, 50, 10.5, 4.0, 56, "HIGH", "Under Evaluation"),
        ("HAB-014", "Pine Heights", "Solan", "Himachal Pradesh", 330, 85, 30.9045, 77.0967, "Extreme Rainfall", 1520, 85, 4.2, 2.1, 22, "LOW", "Safe"),
        ("HAB-015", "Riverbend Settlement", "Cuttack", "Odisha", 610, 215, 20.4625, 85.8828, "Coastal Erosion", 25, 55, 8.8, 4.5, 42, "MODERATE", "Monitoring")
    ]
    
    for h in habitations:
        cursor.execute('''
            INSERT INTO habitations (
                habitation_code, name, district, state, population, vulnerable_population,
                latitude, longitude, primary_hazard, elevation, road_accessibility,
                nearest_hospital_km, nearest_school_km, current_risk_score, risk_category, relocation_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', h)

    # Sample Hazards
    cursor.execute('''
        INSERT INTO hazards (habitation_id, hazard_type, severity_level, rainfall_exposure, slope_degrees, historical_frequency, distance_from_hazard_km)
        VALUES 
        (1, 'Landslide', 'High', 85, 42, 75, 0.4),
        (2, 'Flood', 'Critical', 92, 12, 88, 0.2),
        (3, 'Cloudburst', 'High', 78, 35, 65, 0.8),
        (4, 'Extreme Rainfall', 'High', 80, 28, 60, 1.2),
        (6, 'Coastal Erosion', 'Critical', 88, 5, 82, 0.1),
        (10, 'Cloudburst', 'Critical', 90, 48, 80, 0.3)
    ''')

    # Sample Safe Zones (8 safer locations with carrying capacity)
    safe_zones = [
        ("SZ-101", "Safe Haven Alpha", "Mandi High Plateau", "Mandi", 45000, 1500, 620, 85, 3.5, 1.8, 100, 100, 15, 91, 31.7400, 76.9600),
        ("SZ-102", "Resilient Ridge Site B", "Chamoli Ridge Ground", "Chamoli", 36000, 1200, 450, 78, 4.2, 2.5, 90, 90, 20, 88, 30.4500, 79.3500),
        ("SZ-103", "Highland Emergency Base", "Shimla Crest Center", "Shimla", 60000, 2000, 890, 92, 2.1, 1.2, 100, 100, 10, 94, 31.1300, 77.2000),
        ("SZ-104", "Valley Support Ground", "Kullu Central Plain", "Kullu", 50000, 1800, 1100, 80, 3.0, 2.0, 95, 95, 25, 82, 31.9800, 77.1400),
        ("SZ-105", "Coastal Safe Shelter West", "Kendrapara High Ground", "Kendrapara", 30000, 1000, 380, 88, 4.8, 2.2, 90, 90, 18, 85, 20.5400, 86.4600),
        ("SZ-106", "Southern Transit Hub", "Pathanamthitta Center", "Pathanamthitta", 42000, 1400, 700, 82, 3.8, 1.5, 85, 90, 22, 79, 9.2900, 76.8200),
        ("SZ-107", "Darjeeling Relief Campus", "Darjeeling Mesa", "Darjeeling", 28000, 950, 290, 86, 2.8, 1.9, 90, 85, 15, 87, 27.0700, 88.2900),
        ("SZ-108", "Nilgiris Buffer Site", "Nilgiris Safe Enclave", "Nilgiris", 48000, 1600, 500, 95, 2.0, 1.0, 100, 100, 12, 90, 11.4400, 76.7300)
    ]
    
    for sz in safe_zones:
        cursor.execute('''
            INSERT INTO safe_zones (
                site_code, name, location_name, district, area_sqm, estimated_capacity,
                current_occupancy, road_accessibility, nearest_hospital_km, nearest_school_km,
                water_availability, power_availability, hazard_exposure, suitability_score, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sz)

    # Initial Alerts based on High/Critical Risk
    alerts = [
        (1, "Critical Risk Score", "Critical", 78, "Hillview Hamlet assessed with high landslide susceptibility score of 78/100. Immediate relocation planning recommended."),
        (2, "Critical Risk Score", "Critical", 84, "Riverbank Colony flood exposure rating is 84/100. Vulnerable population count is 290."),
        (6, "Coastal Hazard Warning", "Critical", 72, "Coastal Reach experiencing high wave erosion risk score 72/100. Elevation only 15m."),
        (10, "Cloudburst Vulnerability", "Critical", 76, "Valley Point Settlement vulnerable to cloudburst runoff. Nearest hospital is 19.4 km away."),
        (3, "High Hazard Alert", "Warning", 66, "Kaveri Settlement marked HIGH risk (66/100) due to steep slope (35 degrees) and rainfall exposure.")
    ]
    
    for a in alerts:
        cursor.execute('''
            INSERT INTO alerts (habitation_id, alert_type, severity, risk_score, message)
            VALUES (?, ?, ?, ?, ?)
        ''', a)

    # Initial Relocation Plans
    cursor.execute('''
        INSERT INTO relocation_plans (habitation_id, safe_zone_id, population_to_relocate, priority, status, distance_km, suitability_score, recommended_action)
        VALUES 
        (1, 1, 420, 'EMERGENCY', 'Proposed', 4.8, 91, 'Prioritize detailed relocation planning for Hillview Hamlet to Safe Haven Alpha. Verify site infrastructure through field survey.'),
        (2, 6, 680, 'EMERGENCY', 'Under Review', 14.2, 79, 'Allocate 680 seats at Southern Transit Hub. Coordinate emergency transit route.'),
        (6, 5, 850, 'HIGH', 'Proposed', 6.5, 85, 'Plan staged evacuation of 850 residents to Coastal Safe Shelter West.')
    ''')

# ==========================================
# MATHEMATICAL RISK & RELOCATION LOGIC
# ==========================================

def calculate_risk_score(data):
    """
    Transparent mathematical calculation of risk score (0-100).
    """
    hazard_exposure = float(data.get("hazard_exposure", 50))
    rainfall_exposure = float(data.get("rainfall_exposure", 50))
    slope = float(data.get("slope", 20))
    vulnerable_pop_pct = float(data.get("vulnerable_population", 30))
    historical_freq = float(data.get("historical_frequency", 40))
    road_access = float(data.get("road_accessibility", 50))
    emergency_dist = float(data.get("emergency_distance", 20))
    infra_condition = float(data.get("infrastructure_condition", 50))
    
    accessibility_risk = 100.0 - road_access
    infra_risk = 100.0 - infra_condition
    
    score = (
        0.25 * hazard_exposure +
        0.15 * rainfall_exposure +
        0.12 * slope +
        0.15 * vulnerable_pop_pct +
        0.12 * historical_freq +
        0.10 * accessibility_risk +
        0.06 * emergency_dist +
        0.05 * infra_risk
    )
    
    score = round(min(100.0, max(0.0, score)), 1)
    
    if score < 30:
        category = "LOW"
        priority = "LOW"
    elif score < 50:
        category = "MODERATE"
        priority = "MEDIUM"
    elif score < 70:
        category = "HIGH"
        priority = "HIGH"
    else:
        category = "CRITICAL"
        priority = "EMERGENCY"
        
    return {
        "risk_score": score,
        "risk_category": category,
        "priority": priority,
        "factors": {
            "hazard_exposure": hazard_exposure,
            "population_vulnerability": vulnerable_pop_pct,
            "historical_risk": historical_freq,
            "infrastructure_risk": round(infra_risk, 1),
            "accessibility_risk": round(accessibility_risk, 1)
        }
    }

def get_ml_prediction(inputs):
    """
    Runs prediction using trained Scikit-learn model if available.
    Falls back to mathematical model if file missing.
    """
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            feature_names = [
                "hazard_exposure", "rainfall_exposure", "slope",
                "population_density", "vulnerable_population", "historical_frequency",
                "road_accessibility", "emergency_distance", "infrastructure_condition", "elevation"
            ]
            
            # Prepare feature vector
            vector = [float(inputs.get(f, 50)) for f in feature_names]
            X_input = pd.DataFrame([vector], columns=feature_names)
            
            pred_class = model.predict(X_input)[0]
            probs = model.predict_proba(X_input)[0]
            max_conf = round(float(np.max(probs)), 2)
            
            math_res = calculate_risk_score(inputs)
            
            return {
                "risk_category": pred_class,
                "confidence": max_conf,
                "risk_score": math_res["risk_score"],
                "priority": math_res["priority"],
                "is_ml": True,
                "factors": math_res["factors"]
            }
        except Exception as e:
            print(f"ML Model prediction error: {e}")
            
    # Fallback if model not loaded
    math_res = calculate_risk_score(inputs)
    math_res["confidence"] = 0.85
    math_res["is_ml"] = False
    return math_res

def match_relocation_sites(habitation_id):
    """
    Ranks safe zones for a habitation based on carrying capacity, distance, and suitability.
    """
    habitation = query_db("SELECT * FROM habitations WHERE id = ?", (habitation_id,), one=True)
    if not habitation:
        return None
        
    pop_to_relocate = habitation["population"]
    h_lat, h_lon = habitation["latitude"], habitation["longitude"]
    
    safe_zones = query_db("SELECT * FROM safe_zones")
    candidates = []
    
    for sz in safe_zones:
        remaining_capacity = sz["estimated_capacity"] - sz["current_occupancy"]
        
        # Calculate Haversine distance in km
        lat1, lon1, lat2, lon2 = map(np.radians, [h_lat, h_lon, sz["latitude"], sz["longitude"]])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        dist_km = round(float(6371 * c), 1)
        
        # Capacity check
        capacity_suitable = remaining_capacity >= pop_to_relocate
        occupancy_rate = round((sz["current_occupancy"] / sz["estimated_capacity"]) * 100, 1)
        
        # Weighted site ranking score
        # High suitability, low distance, high remaining capacity margin
        dist_score = max(0, 100 - (dist_km * 3))
        match_rank = round((0.5 * sz["suitability_score"]) + (0.3 * dist_score) + (0.2 * (100 - occupancy_rate)), 1)
        
        candidates.append({
            "site_id": sz["id"],
            "site_code": sz["site_code"],
            "name": sz["name"],
            "location_name": sz["location_name"],
            "district": sz["district"],
            "total_capacity": sz["estimated_capacity"],
            "current_occupancy": sz["current_occupancy"],
            "remaining_capacity": remaining_capacity,
            "occupancy_rate": occupancy_rate,
            "suitability_score": sz["suitability_score"],
            "distance_km": dist_km,
            "capacity_fits": capacity_suitable,
            "match_rank": match_rank,
            "road_access": sz["road_accessibility"],
            "water_access": sz["water_availability"],
            "power_access": sz["power_availability"]
        })
        
    # Sort candidates by capacity availability first, then match rank
    candidates.sort(key=lambda x: (x["capacity_fits"], x["match_rank"]), reverse=True)
    
    recommendation_text = ""
    if candidates and candidates[0]["capacity_fits"]:
        top = candidates[0]
        recommendation_text = (
            f"Recommended Site: '{top['name']}' located {top['distance_km']} km away in {top['district']}. "
            f"It has {top['remaining_capacity']} remaining capacity seats available (relocation needs {pop_to_relocate} residents) "
            f"with a high suitability score of {top['suitability_score']}%. Field verification required prior to execution."
        )
    else:
        recommendation_text = (
            "No single safe zone currently possesses sufficient remaining carrying capacity. "
            "Consider split relocation across multiple sites or expanding temporary emergency capacity."
        )
        
    return {
        "habitation": dict(habitation),
        "population_to_relocate": pop_to_relocate,
        "recommended_action": recommendation_text,
        "candidates": candidates
    }

# ==========================================
# AUTHENTICATION DECORATOR
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access the system module.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# PUBLIC WEB ROUTES
# ==========================================

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if user and user["password"] == password:
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "name": user["name"],
                "role": user["role"]
            }
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. (Demo: admin / admin123)", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))

# ==========================================
# PROTECTED WEB ROUTES
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/habitations")
@login_required
def habitations():
    return render_template("habitations.html")

@app.route("/hazards")
@login_required
def hazards():
    return render_template("hazards.html")

@app.route("/risk-analysis")
@login_required
def risk_analysis():
    # Read ML model metadata if available
    metadata = {}
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass
    return render_template("risk_analysis.html", metadata=metadata)

@app.route("/safe-zones")
@login_required
def safe_zones():
    return render_template("safe_zones.html")

@app.route("/relocation")
@login_required
def relocation():
    return render_template("relocation.html")

@app.route("/alerts")
@login_required
def alerts():
    return render_template("alerts.html")

@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")

@app.route("/about")
@login_required
def about():
    metadata = {}
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass
    return render_template("about.html", metadata=metadata)

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route("/api/dashboard")
@login_required
def api_dashboard():
    total_habitations = query_db("SELECT COUNT(*) FROM habitations", one=True)[0]
    high_risk = query_db("SELECT COUNT(*) FROM habitations WHERE risk_category IN ('HIGH', 'CRITICAL')", one=True)[0]
    red_zones = query_db("SELECT COUNT(*) FROM habitations WHERE current_risk_score >= 70", one=True)[0]
    relocation_req = query_db("SELECT COUNT(*) FROM habitations WHERE relocation_status = 'Relocation Required'", one=True)[0]
    
    sz_capacity = query_db("SELECT SUM(estimated_capacity), SUM(current_occupancy) FROM safe_zones", one=True)
    total_cap = sz_capacity[0] or 0
    curr_occ = sz_capacity[1] or 0
    available_cap = max(0, total_cap - curr_occ)
    
    avg_risk = query_db("SELECT AVG(current_risk_score) FROM habitations", one=True)[0]
    avg_risk = round(avg_risk, 1) if avg_risk else 0
    
    # Risk Distribution for Chart.js
    risk_dist_rows = query_db("SELECT risk_category, COUNT(*) as count FROM habitations GROUP BY risk_category")
    risk_dist = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for r in risk_dist_rows:
        risk_dist[r["risk_category"]] = r["count"]
        
    # Hazard Distribution for Chart.js
    hazard_dist_rows = query_db("SELECT primary_hazard, COUNT(*) as count FROM habitations GROUP BY primary_hazard")
    hazard_dist = {r["primary_hazard"]: r["count"] for r in hazard_dist_rows}
    
    # Relocation Status Distribution
    status_dist_rows = query_db("SELECT relocation_status, COUNT(*) as count FROM habitations GROUP BY relocation_status")
    status_dist = {r["relocation_status"]: r["count"] for r in status_dist_rows}
    
    # Recent Habitations Table
    recent_habs = [dict(r) for r in query_db("SELECT * FROM habitations ORDER BY current_risk_score DESC LIMIT 8")]
    
    # Active Alerts
    recent_alerts = [dict(r) for r in query_db("SELECT a.*, h.name as habitation_name FROM alerts a JOIN habitations h ON a.habitation_id = h.id ORDER BY a.timestamp DESC LIMIT 5")]
    
    return jsonify({
        "stats": {
            "total_habitations": total_habitations,
            "high_risk_habitations": high_risk,
            "red_zone_habitations": red_zones,
            "relocation_required": relocation_req,
            "total_safe_capacity": total_cap,
            "current_safe_occupancy": curr_occ,
            "available_safe_capacity": available_cap,
            "average_risk_score": avg_risk
        },
        "charts": {
            "risk_distribution": risk_dist,
            "hazard_distribution": hazard_dist,
            "relocation_status": status_dist
        },
        "recent_habitations": recent_habs,
        "recent_alerts": recent_alerts
    })

@app.route("/api/habitations")
@login_required
def api_habitations():
    risk_filter = request.args.get("risk")
    hazard_filter = request.args.get("hazard")
    search = request.args.get("search", "").strip()
    
    query = "SELECT * FROM habitations WHERE 1=1"
    params = []
    
    if risk_filter and risk_filter != "ALL":
        query += " AND risk_category = ?"
        params.append(risk_filter)
    if hazard_filter and hazard_filter != "ALL":
        query += " AND primary_hazard = ?"
        params.append(hazard_filter)
    if search:
        query += " AND (name LIKE ? OR district LIKE ? OR habitation_code LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY current_risk_score DESC"
    habs = [dict(r) for r in query_db(query, params)]
    return jsonify(habs)

@app.route("/api/habitations/<int:hab_id>")
@login_required
def api_habitation_detail(hab_id):
    hab = query_db("SELECT * FROM habitations WHERE id = ?", (hab_id,), one=True)
    if not hab:
        return jsonify({"error": "Habitation not found"}), 404
        
    hazards_list = [dict(r) for r in query_db("SELECT * FROM hazards WHERE habitation_id = ?", (hab_id,))]
    assessments = [dict(r) for r in query_db("SELECT * FROM risk_assessments WHERE habitation_id = ? ORDER BY date_assessed DESC", (hab_id,))]
    alerts_list = [dict(r) for r in query_db("SELECT * FROM alerts WHERE habitation_id = ? ORDER BY timestamp DESC", (hab_id,))]
    
    return jsonify({
        "habitation": dict(hab),
        "hazards": hazards_list,
        "risk_assessments": assessments,
        "alerts": alerts_list
    })

@app.route("/api/hazards")
@login_required
def api_hazards():
    hazards_list = [dict(r) for r in query_db("SELECT h.*, hab.name as habitation_name, hab.district FROM hazards h JOIN habitations hab ON h.habitation_id = hab.id ORDER BY h.created_at DESC")]
    return jsonify(hazards_list)

@app.route("/api/risk/predict", methods=["POST"])
@login_required
def api_risk_predict():
    data = request.json or request.form
    if not data:
        return jsonify({"error": "Missing input JSON"}), 400
        
    # Input validation
    try:
        inputs = {
            "hazard_exposure": float(data.get("hazard_exposure", 50)),
            "rainfall_exposure": float(data.get("rainfall_exposure", 50)),
            "slope": float(data.get("slope", 20)),
            "population_density": float(data.get("population_density", 50)),
            "vulnerable_population": float(data.get("vulnerable_population", 30)),
            "historical_frequency": float(data.get("historical_frequency", 40)),
            "road_accessibility": float(data.get("road_accessibility", 50)),
            "emergency_distance": float(data.get("emergency_distance", 20)),
            "infrastructure_condition": float(data.get("infrastructure_condition", 50)),
            "elevation": float(data.get("elevation", 500))
        }
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric input parameters: {e}"}), 400
        
    # Generate ML + Mathematical prediction
    prediction = get_ml_prediction(inputs)
    
    # Save log to predictions table
    habitation_id = data.get("habitation_id")
    execute_db(
        "INSERT INTO predictions (habitation_id, inputs_json, risk_category, confidence, risk_score, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (habitation_id, json.dumps(inputs), prediction["risk_category"], prediction["confidence"], prediction["risk_score"], prediction["priority"])
    )
    
    # Generate automatic alert if risk is High or Critical
    if prediction["risk_score"] >= 50 and habitation_id:
        hab = query_db("SELECT name FROM habitations WHERE id = ?", (habitation_id,), one=True)
        hab_name = hab["name"] if hab else "Assessed Settlement"
        severity = "Critical" if prediction["risk_score"] >= 70 else "Warning"
        msg = f"AI Risk Predictor generated {severity.upper()} risk alert for {hab_name}. Risk score: {prediction['risk_score']}/100 ({prediction['risk_category']})."
        execute_db(
            "INSERT INTO alerts (habitation_id, alert_type, severity, risk_score, message) VALUES (?, ?, ?, ?, ?)",
            (habitation_id, f"Predicted {prediction['risk_category']} Risk", severity, prediction["risk_score"], msg)
        )
        
    return jsonify(prediction)

@app.route("/api/risk/history")
@login_required
def api_risk_history():
    preds = [dict(r) for r in query_db("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 20")]
    return jsonify(preds)

@app.route("/api/safe-zones")
@login_required
def api_safe_zones():
    sz_list = [dict(r) for r in query_db("SELECT * FROM safe_zones ORDER BY suitability_score DESC")]
    for sz in sz_list:
        sz["remaining_capacity"] = max(0, sz["estimated_capacity"] - sz["current_occupancy"])
        sz["occupancy_rate"] = round((sz["current_occupancy"] / sz["estimated_capacity"]) * 100, 1)
    return jsonify(sz_list)

@app.route("/api/safe-zones/<int:sz_id>")
@login_required
def api_safe_zone_detail(sz_id):
    sz = query_db("SELECT * FROM safe_zones WHERE id = ?", (sz_id,), one=True)
    if not sz:
        return jsonify({"error": "Safe zone not found"}), 404
    sz_dict = dict(sz)
    sz_dict["remaining_capacity"] = max(0, sz_dict["estimated_capacity"] - sz_dict["current_occupancy"])
    sz_dict["occupancy_rate"] = round((sz_dict["current_occupancy"] / sz_dict["estimated_capacity"]) * 100, 1)
    return jsonify(sz_dict)

@app.route("/api/relocation/<int:habitation_id>")
@login_required
def api_relocation_recommendation(habitation_id):
    res = match_relocation_sites(habitation_id)
    if not res:
        return jsonify({"error": "Habitation not found"}), 404
    return jsonify(res)

@app.route("/api/alerts")
@login_required
def api_alerts():
    alerts_list = [dict(r) for r in query_db("SELECT a.*, h.name as habitation_name, h.district FROM alerts a JOIN habitations h ON a.habitation_id = h.id ORDER BY a.timestamp DESC")]
    return jsonify(alerts_list)

@app.route("/api/alerts/<int:alert_id>/status", methods=["POST"])
@login_required
def api_alert_status(alert_id):
    data = request.json or {}
    new_status = data.get("status", "Acknowledged")
    if new_status not in ["New", "Acknowledged", "Resolved"]:
        return jsonify({"error": "Invalid status value"}), 400
        
    execute_db("UPDATE alerts SET status = ? WHERE id = ?", (new_status, alert_id))
    return jsonify({"success": True, "alert_id": alert_id, "status": new_status})

@app.route("/api/reports")
@login_required
def api_reports():
    total_habs = query_db("SELECT COUNT(*) FROM habitations", one=True)[0]
    critical_habs = query_db("SELECT COUNT(*) FROM habitations WHERE current_risk_score >= 70", one=True)[0]
    high_habs = query_db("SELECT COUNT(*) FROM habitations WHERE risk_category = 'HIGH'", one=True)[0]
    reloc_req = query_db("SELECT COUNT(*) FROM habitations WHERE relocation_status = 'Relocation Required'", one=True)[0]
    
    sz_summary = query_db("SELECT SUM(estimated_capacity), SUM(current_occupancy) FROM safe_zones", one=True)
    tot_cap = sz_summary[0] or 0
    curr_occ = sz_summary[1] or 0
    rem_cap = max(0, tot_cap - curr_occ)
    
    red_zone_habs = [dict(r) for r in query_db("SELECT * FROM habitations WHERE current_risk_score >= 50 ORDER BY current_risk_score DESC")]
    safe_zones_list = [dict(r) for r in query_db("SELECT * FROM safe_zones ORDER BY suitability_score DESC")]
    for sz in safe_zones_list:
        sz["remaining_capacity"] = max(0, sz["estimated_capacity"] - sz["current_occupancy"])
        sz["occupancy_rate"] = round((sz["current_occupancy"] / sz["estimated_capacity"]) * 100, 1)
        
    reloc_plans = [dict(r) for r in query_db('''
        SELECT rp.*, h.name as habitation_name, h.district, sz.name as safe_zone_name 
        FROM relocation_plans rp
        JOIN habitations h ON rp.habitation_id = h.id
        JOIN safe_zones sz ON rp.safe_zone_id = sz.id
        ORDER BY rp.created_at DESC
    ''')]
    
    return jsonify({
        "summary": {
            "total_habitations": total_habs,
            "critical_habitations": critical_habs,
            "high_risk_habitations": high_habs,
            "relocation_required_count": reloc_req,
            "total_safe_capacity": tot_cap,
            "current_safe_occupancy": curr_occ,
            "remaining_safe_capacity": rem_cap,
            "generated_date": datetime.datetime.now().strftime("%B %d, %Y - %H:%M:%S")
        },
        "red_zone_habitations": red_zone_habs,
        "safe_zones": safe_zones_list,
        "relocation_plans": reloc_plans
    })

# Initialize DB on start
with app.app_context():
    init_db()

if __name__ == "__main__":
    print("\nStarting SafeZone Disaster Management Application...")
    print("Local Server Running at: http://127.0.0.1:5000")
    print("Demo Admin Credentials: admin / admin123")
    app.run(debug=True, port=5000)
