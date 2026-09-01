import os
import json
import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

def generate_synthetic_data(num_samples=5000, seed=42):
    np.random.seed(seed)
    
    # 10 risk-related feature factors
    hazard_exposure = np.random.uniform(10, 100, num_samples)
    rainfall_exposure = np.random.uniform(10, 100, num_samples)
    slope = np.random.uniform(0, 60, num_samples)
    population_density = np.random.uniform(5, 100, num_samples)
    vulnerable_population = np.random.uniform(5, 80, num_samples)
    historical_frequency = np.random.uniform(0, 100, num_samples)
    road_accessibility = np.random.uniform(10, 100, num_samples)
    emergency_distance = np.random.uniform(5, 100, num_samples)
    infrastructure_condition = np.random.uniform(10, 100, num_samples)
    elevation = np.random.uniform(10, 100, num_samples)
    
    accessibility_risk = 100 - road_accessibility
    infra_risk = 100 - infrastructure_condition
    
    # Mathematical composite risk index calculation
    raw_risk = (
        0.25 * hazard_exposure +
        0.15 * rainfall_exposure +
        0.12 * slope +
        0.15 * vulnerable_population +
        0.12 * historical_frequency +
        0.10 * accessibility_risk +
        0.06 * emergency_distance +
        0.05 * infra_risk
    )
    
    # Add subtle realistic noise
    noise = np.random.normal(0, 2.5, num_samples)
    final_score = np.clip(raw_risk + noise, 0, 100)
    
    categories = []
    for score in final_score:
        if score < 30:
            categories.append("LOW")
        elif score < 50:
            categories.append("MODERATE")
        elif score < 70:
            categories.append("HIGH")
        else:
            categories.append("CRITICAL")
            
    df = pd.DataFrame({
        "hazard_exposure": np.round(hazard_exposure, 1),
        "rainfall_exposure": np.round(rainfall_exposure, 1),
        "slope": np.round(slope, 1),
        "population_density": np.round(population_density, 1),
        "vulnerable_population": np.round(vulnerable_population, 1),
        "historical_frequency": np.round(historical_frequency, 1),
        "road_accessibility": np.round(road_accessibility, 1),
        "emergency_distance": np.round(emergency_distance, 1),
        "infrastructure_condition": np.round(infrastructure_condition, 1),
        "elevation": np.round(elevation, 1),
        "risk_category": categories
    })
    
    return df

def train_and_save_model():
    print("=" * 60)
    print("SafeZone Risk Prediction Model Training")
    print("=" * 60)
    
    print("\n1. Generating synthetic training dataset (5,000 samples)...")
    df = generate_synthetic_data(num_samples=5000, seed=42)
    
    # Create output directories
    os.makedirs("model", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    
    # Save dataset CSV for reference
    df.to_csv("model/synthetic_risk_dataset.csv", index=False)
    print("   Dataset saved to 'model/synthetic_risk_dataset.csv'")
    
    feature_names = [
        "hazard_exposure", "rainfall_exposure", "slope",
        "population_density", "vulnerable_population", "historical_frequency",
        "road_accessibility", "emergency_distance", "infrastructure_condition", "elevation"
    ]
    
    labels_order = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    
    X = df[feature_names]
    y = df["risk_category"]
    
    print("\n2. Splitting dataset into training (80%) and testing (20%) sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("\n3. Training RandomForestClassifier model...")
    clf = RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    print("\n4. Evaluating model performance on test set...")
    y_pred = clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    
    report_text = classification_report(y_test, y_pred, labels=labels_order, target_names=labels_order)
    report_dict = classification_report(y_test, y_pred, labels=labels_order, target_names=labels_order, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=labels_order)
    
    print(f"\n---> Empirical Model Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:\n", report_text)
    print("Confusion Matrix:\n", cm)
    
    importances = dict(zip(feature_names, [round(float(imp), 4) for imp in clf.feature_importances_]))
    print("\nFeature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {feat:25s}: {imp:.4f}")
        
    model_path = "model/risk_model.pkl"
    joblib.dump(clf, model_path)
    print(f"\n5. Saved trained model to '{model_path}'")
    
    metadata = {
        "model_name": "RandomForestClassifier",
        "num_estimators": 120,
        "max_depth": 12,
        "features": feature_names,
        "target_classes": labels_order,
        "accuracy": round(accuracy, 4),
        "accuracy_percentage": f"{accuracy * 100:.2f}%",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_importances": importances,
        "trained_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "classification_report": report_dict
    }
    
    metadata_path = "model/risk_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"   Saved model metadata to '{metadata_path}'")
    print("=" * 60)
    print("Training Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    train_and_save_model()
