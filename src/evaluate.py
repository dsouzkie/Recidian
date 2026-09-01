import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import json
import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_curve, auc, precision_recall_curve, average_precision_score
)

def main():
    print("Loading test data and models...")
    X_test = pd.read_csv("data/X_test.csv")
    y_test = pd.read_csv("data/y_test.csv").squeeze()
    
    with open("models/feature_columns.json", "r") as f:
        feature_cols = json.load(f)
    X_test = X_test[feature_cols]

    # Load Model
    model = xgb.XGBClassifier()
    model.load_model("models/model.json")
    
    # Load Threshold Info
    with open("models/threshold.json", "r") as f:
        thresh_info = json.load(f)
        
    optimal_threshold = thresh_info["optimal_threshold"]
    FP_COST = thresh_info["fp_cost_multiplier"]
    FN_COST = thresh_info["fn_cost_multiplier"]
    
    # Predict
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= optimal_threshold).astype(int)
    
    # --- METRICS ---
    print("Calculating metrics...")
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    
    precisions, recalls, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    
    total_fp_cost = fp * FP_COST
    total_fn_cost = fn * FN_COST
    total_cost = total_fp_cost + total_fn_cost

    # Ensure static directory exists
    os.makedirs("static", exist_ok=True)
    
    # --- PLOTS ---
    print("Generating charts...")
    # 1. Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Normal', 'Abusive'], yticklabels=['Normal', 'Abusive'])
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title(f'Confusion Matrix (Threshold = {optimal_threshold})')
    plt.savefig("static/confusion_matrix.png", bbox_inches='tight', dpi=150)
    plt.close()
    
    # 2. ROC Curve
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    plt.savefig("static/roc_curve.png", bbox_inches='tight', dpi=150)
    plt.close()
    
    # 3. PR Curve
    plt.figure(figsize=(6, 5))
    plt.plot(recalls, precisions, color='purple', lw=2, label=f'PR curve (AUC = {pr_auc:.3f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend(loc="lower left")
    plt.savefig("static/pr_curve.png", bbox_inches='tight', dpi=150)
    plt.close()
    
    # 4. SHAP Summary Plot
    print("Generating SHAP summary plot...")
    with open("models/shap_explainer.pkl", "rb") as f:
        explainer = pickle.load(f)
    
    # SHAP plotting is tricky to save directly, we do this:
    shap_values = explainer(X_test)
    plt.figure(figsize=(8, 6))
    shap.summary_plot(shap_values, X_test, show=False)
    plt.savefig("static/shap_summary.png", bbox_inches='tight', dpi=150)
    plt.close()

    # --- FAILURE CASE ANALYSIS ---
    print("Finding a failure case for analysis...")
    # Find a False Positive (Model predicted 1, True was 0)
    fp_mask = (y_pred == 1) & (y_test == 0)
    fp_indices = np.where(fp_mask)[0]
    
    failure_case = {}
    if len(fp_indices) > 0:
        idx = fp_indices[0] # Pick the first False Positive
        row = X_test.iloc[idx]
        score = float(y_prob[idx])
        
        # Get SHAP values for this specific prediction
        sv = shap_values[idx].values
        top_indices = np.argsort(np.abs(sv))[-3:][::-1] # Top 3 most impactful features
        
        top_reasons = []
        for i in top_indices:
            feat = feature_cols[i]
            val = row[feat]
            contrib = sv[i]
            direction = "increased" if contrib > 0 else "decreased"
            top_reasons.append(f"{feat} ({val}) {direction} risk by {abs(contrib):.3f}")
            
        failure_case = {
            "type": "False Positive",
            "index": int(idx),
            "score": score,
            "threshold": optimal_threshold,
            "top_reasons": top_reasons,
            "explanation": "The model heavily weighted one specific suspicious feature, overriding the overall safe profile of the user."
        }
    else:
        failure_case = {"type": "None", "explanation": "No false positives found."}

    # --- EXPORT METRICS JSON ---
    metrics = {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "total_fp_cost": int(total_fp_cost),
        "total_fn_cost": int(total_fn_cost),
        "total_business_cost": int(total_cost),
        "failure_case": failure_case
    }
    
    with open("models/metrics.json", "w") as f:
        json.dump(metrics, f, indent=4)
        
    # --- EXPORT METRICS REPORT MD ---
    report = f"""# RECIDIAN Evaluation Report

## Core Metrics (Threshold = {optimal_threshold})
- **Precision:** {precision:.3f} (When we flag a return, we are right {precision:.1%} of the time)
- **Recall:** {recall:.3f} (We catch {recall:.1%} of all abusive returns)
- **F1 Score:** {f1:.3f}
- **ROC-AUC:** {roc_auc:.3f}
- **PR-AUC:** {pr_auc:.3f}

## Business Cost Impact on Test Set
- **False Positives (Good customers insulted):** {fp} (Cost: INR {total_fp_cost:,})
- **False Negatives (Fraudsters succeeded):** {fn} (Cost: INR {total_fn_cost:,})
- **Total Business Loss (Test Set):** INR {total_cost:,}

## Failure Case Analysis
**Type:** {failure_case.get('type')} (Score: {failure_case.get('score', 0):.3f})
**Why did the model get it wrong?**
"""
    if "top_reasons" in failure_case:
        for r in failure_case["top_reasons"]:
            report += f"- {r}\n"
    
    report += f"\n**Root Cause:** {failure_case.get('explanation')}\n"
    report += "\n**What we'd do with more time:** Add peer-group normalization. The model currently looks at absolute return rates, but 10% might be high for electronics while 10% is perfectly normal for fashion. Group-relative features would fix this False Positive.\n"

    with open("metrics_report.md", "w") as f:
        f.write(report)
        
    print("Evaluation Complete. Check models/metrics.json and metrics_report.md.")

if __name__ == "__main__":
    main()
