import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import json
import pickle
import os

def main():
    print("Loading training data...")
    X_train = pd.read_csv("data/X_train.csv")
    y_train = pd.read_csv("data/y_train.csv").squeeze() # convert to Series
    X_test = pd.read_csv("data/X_test.csv")
    y_test = pd.read_csv("data/y_test.csv").squeeze()

    # Load feature columns to ensure ordering
    with open("models/feature_columns.json", "r") as f:
        feature_cols = json.load(f)
    
    # Ensure X_train matches feature_cols order exactly
    X_train = X_train[feature_cols]
    X_test = X_test[feature_cols]

    print(f"Training XGBoost Model on {len(X_train)} samples, {len(feature_cols)} features...")
    # Handle early_stopping_rounds properly in newer XGBoost versions
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        eval_metric='logloss',
        random_state=42
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=10
    )
    
    print("\nSetting up SHAP Explainer...")
    # XGBoost + SHAP on tree models
    explainer = shap.TreeExplainer(model)
    
    # Test SHAP on a few rows to verify it works
    sample = X_test.iloc[:5]
    shap_values = explainer.shap_values(sample)
    print("SHAP verification successful. Shape:", np.array(shap_values).shape)

    print("\nOptimizing Classification Threshold for Business Cost...")
    # FP Cost = ₹2,150 (Good customer insulated, false positive friction)
    # FN Cost = ₹1,085 (Fraudster got away with average order value loss)
    FP_COST = 2150
    FN_COST = 1085
    
    # Predict probabilities on test set
    y_prob = model.predict_proba(X_test)[:, 1]
    
    thresholds = np.linspace(0.01, 0.99, 99)
    curve_data = []
    
    best_threshold = 0.5
    min_cost = float('inf')
    
    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)
        
        # Calculate metrics
        tp = np.sum((y_pred == 1) & (y_test == 1))
        fp = np.sum((y_pred == 1) & (y_test == 0))
        fn = np.sum((y_pred == 0) & (y_test == 1))
        tn = np.sum((y_pred == 0) & (y_test == 0))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        total_fp_cost = fp * FP_COST
        total_fn_cost = fn * FN_COST
        total_cost = total_fp_cost + total_fn_cost
        
        curve_data.append({
            "threshold": round(t, 2),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "fp_count": int(fp),
            "fn_count": int(fn),
            "fp_cost": int(total_fp_cost),
            "fn_cost": int(total_fn_cost),
            "total_cost": int(total_cost)
        })
        
        if total_cost < min_cost:
            min_cost = total_cost
            best_threshold = t
            
    print(f"Optimal Threshold: {best_threshold:.2f} (Total Cost: INR {min_cost:,})")
    
    # Save artifacts
    print("\nSaving Models and Thresholds to disk...")
    os.makedirs("models", exist_ok=True)
    
    model.save_model("models/model.json")
    
    with open("models/shap_explainer.pkl", "wb") as f:
        pickle.dump(explainer, f)
        
    with open("models/threshold.json", "w") as f:
        json.dump({"optimal_threshold": round(best_threshold, 2), "fp_cost_multiplier": FP_COST, "fn_cost_multiplier": FN_COST}, f)
        
    with open("models/threshold_curve.json", "w") as f:
        json.dump(curve_data, f, indent=4)
        
    print("Block 5 Complete! Model, SHAP Explainer, and Thresholds saved.")

if __name__ == "__main__":
    main()
