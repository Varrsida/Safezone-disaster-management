# SafeZone: Hazard Assessment and Relocation Planning System

**SIH 2026 Problem Statement ID:** SIH26191  
**Organization:** Ministry of Home Affairs  
**Department:** National Disaster Response Force (NDRF), DM Division  
**Category:** Software  
**Theme:** Disaster Management  

---

## LIVE DEMO : https://safezone-disaster-management.onrender.com/

## PROTOTYPE : https://drive.google.com/file/d/13G09CEGG2MlxUiVKd0lH1t7dUkoFSUNe/view?usp=drive_link

---

## 1. Executive Summary

**SafeZone** is an educational decision-support software prototype designed to assist disaster management authorities and NDRF planners in:
1. Identifying vulnerable habitations located in high-exposure hazard zones (landslides, floods, cloudbursts, coastal erosion, extreme rainfall).
2. Transparently calculating mathematical risk scores (0–100) and classifying habitations into **LOW**, **MODERATE**, **HIGH**, and **CRITICAL** risk categories.
3. Predicting risk levels using a trained Scikit-learn **RandomForestClassifier** model.
4. Evaluating recipient safe zones for available land area, infrastructure connections (water/power), accessibility, and proximity to hospitals and schools.
5. Auditing carrying capacity (designed capacity vs. current occupancy) to prevent overcrowding during emergency evacuations.
6. Matching vulnerable populations with optimal safe zones using distance matrix calculations and ranking suitability.
7. Generating administrative alert streams and printable executive summary reports.

---

## 2. Core Decision Workflow

```
Hazard Data & Exposure
          ↓
Multi-Factor Risk Assessment (0–100 Score)
          ↓
Vulnerable Habitation Identification
          ↓
Red-Zone Classification (Risk ≥ 70)
          ↓
Population Vulnerability & Road Isolation Assessment
          ↓
Safe Location Identification & Utility Inspection
          ↓
Carrying Capacity Assessment (Available Margin)
          ↓
Relocation Priority & Site Ranking Engine
          ↓
Recommended Action & Field Verification Report
```

---

## 3. Technology Stack

- **Frontend:** HTML5, CSS3, Vanilla JavaScript (No React, Vue, Angular, Bootstrap, or Tailwind).
- **Backend:** Python 3.13, Flask.
- **Data & AI:** Python, Pandas, NumPy, Scikit-learn, Joblib.
- **Database:** SQLite (`database/safezone.db`).
- **Maps:** Leaflet.js via CDN.
- **Charts:** Chart.js via CDN.

---

## 4. System Installation & Quick Start

### Prerequisites
- Python 3.8 or higher installed.

### Step 1: Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Train Machine Learning Model
```bash
python train_model.py
```
*Outputs `model/risk_model.pkl` and `model/risk_metadata.json` with empirical accuracy (~84.90%).*

### Step 3: Launch Flask Application
```bash
python app.py
```

### Step 4: Access Application Portal
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. Demo Access Credentials

| User Role | Username | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **NDRF Disaster Response Admin** | `admin` | `admin123` | Full access to all 10 system modules & APIs |

---

## 6. Database Architecture

SQLite database located at `database/safezone.db`:

1. `users`: Administrative user credentials and roles.
2. `habitations`: 15+ simulated settlement records with geographical coordinates, elevation, population, vulnerable population, road accessibility, and risk score.
3. `hazards`: Specific hazard exposure parameters (rainfall exposure, slope degrees, historical frequency).
4. `risk_assessments`: Historical multi-factor assessment records.
5. `safe_zones`: 8 candidate safe relocation grounds with designed capacity, occupancy, water, power, and suitability ratings.
6. `relocation_plans`: Active relocation matching records and recommended actions.
7. `alerts`: System-generated warning and critical alert events.
8. `predictions`: Log of ML prediction inputs and outputs.

---

## 7. Machine Learning Methodology

- **Model Type:** `RandomForestClassifier(n_estimators=120, max_depth=12)`
- **Dataset:** 5,000 synthetic records (`model/synthetic_risk_dataset.csv`) generated with realistic noise distributions.
- **Features (10):**
  - `hazard_exposure` (0-100)
  - `rainfall_exposure` (0-100)
  - `slope` (0-60°)
  - `population_density` (0-100)
  - `vulnerable_population` (0-100%)
  - `historical_frequency` (0-100)
  - `road_accessibility` (0-100)
  - `emergency_distance` (0-100 km)
  - `infrastructure_condition` (0-100)
  - `elevation` (0-5000 m)
- **Classes:** `LOW`, `MODERATE`, `HIGH`, `CRITICAL`
- **Empirical Accuracy:** ~84.90% (Calculated dynamically on 20% test split).

---

## 8. Mathematical Risk Score Calculation

```
Risk Score = (
    0.25 * hazard_exposure +
    0.15 * rainfall_exposure +
    0.12 * slope +
    0.15 * vulnerable_population +
    0.12 * historical_frequency +
    0.10 * (100 - road_accessibility) +
    0.06 * emergency_distance +
    0.05 * (100 - infrastructure_condition)
)
```

### Risk Classification Thresholds:
- **0 – 29:** `LOW` (Green)
- **30 – 49:** `MODERATE` (Yellow)
- **50 – 69:** `HIGH` (Orange)
- **70 – 100:** `CRITICAL` (Red)

---

## 9. API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard` | Returns summary statistics, chart distributions, and active alerts |
| `GET` | `/api/habitations` | List habitations with risk and hazard filter parameters |
| `GET` | `/api/habitations/<id>` | Detail record for specific habitation including hazard history |
| `GET` | `/api/hazards` | List hazard assessment records |
| `POST` | `/api/risk/predict` | Executes Scikit-learn model prediction and mathematical score |
| `GET` | `/api/risk/history` | Log of past AI predictions |
| `GET` | `/api/safe-zones` | Returns safe recipient sites with carrying capacity utilization |
| `GET` | `/api/relocation/<id>` | Computes ranked safe zone candidates for a habitation |
| `GET` | `/api/alerts` | List system alerts |
| `POST` | `/api/alerts/<id>/status` | Update alert status (`New`, `Acknowledged`, `Resolved`) |
| `GET` | `/api/reports` | Returns aggregated data for printable administrative reports |


