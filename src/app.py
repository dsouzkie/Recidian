import os
import json
import time
import sqlite3
import pickle
import pandas as pd
import numpy as np
import xgboost as xgb
import razorpay
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from src.rules import apply_rules

# --- APP SETUP ---
app = FastAPI(title="RECIDIAN Risk API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static and data directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Redirect root URL directly to the dashboard."""
    return RedirectResponse(url="/static/index.html")

# --- MODEL LOADING ---
print("Loading models and assets...")
model = xgb.XGBClassifier()
model.load_model("models/model.json")

with open("models/shap_explainer.pkl", "rb") as f:
    explainer = pickle.load(f)

with open("models/threshold.json", "r") as f:
    thresh_info = json.load(f)
    OPTIMAL_THRESHOLD = thresh_info["optimal_threshold"]

with open("models/feature_columns.json", "r") as f:
    FEATURE_COLS = json.load(f)
    
# --- DB SETUP (AUDIT LOG) ---
DB_FILE = "data/audit_log.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            refund_id TEXT,
            score REAL,
            band TEXT,
            triggered_by TEXT,
            reason TEXT,
            shap_values TEXT,
            threshold REAL,
            features_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- RAZORPAY SETUP ---
RZP_KEY = os.getenv("RAZORPAY_KEY_ID", "rzp_test_mock")
RZP_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "mock_secret")

# Only initialize true client if keys are likely real, else use mock
USE_MOCK_RZP = (RZP_KEY == "rzp_test_mock")
if not USE_MOCK_RZP:
    rzp_client = razorpay.Client(auth=(RZP_KEY, RZP_SECRET))
else:
    print("WARNING: Using Mock Razorpay client. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to use live test API.")

# --- WEBHOOK SIMULATION ---
def trigger_webhook_alert(order_id: str, refund_id: str, score: float, reason: str):
    """Simulates sending a webhook/Slack alert to the merchant's fraud team."""
    print("=" * 60)
    print("[WEBHOOK ALERT FIRED] - HIGH RISK REFUND")
    print(f"To: fraud-alerts@merchant.com")
    print(f"Subject: HIGH RISK REFUND DETECTED")
    print(f"Order: {order_id} | Refund: {refund_id}")
    print(f"Risk Score: {score:.2f}")
    print(f"Primary Reason: {reason}")
    print("=" * 60)

# --- PYDANTIC MODELS ---
class ScoringFeatureInput(BaseModel):
    order_id: str
    refund_id: Optional[str] = None
    return_rate_90d: float = 0.0
    orders_last_90d: int = 0
    item_value_percentile: float = 0.5
    promo_code_used: int = 0
    account_age_days: int = 365
    address_mismatch_flag: int = 0
    order_to_return_days: float = 0.0
    same_day_reorder_after_return: int = 0
    category_return_rate_deviation: float = 0.0
    # OHE return reasons
    return_reason_changed_mind: int = 0
    return_reason_damaged: int = 0
    return_reason_no_reason: int = 0
    return_reason_not_as_described: int = 0
    return_reason_wrong_size: int = 0
    return_reason_nan: int = 0

class RzpOrderRequest(BaseModel):
    amount: int
    category: str
    product_name: str
    promo_code: Optional[str] = None

class RzpPaymentRequest(BaseModel):
    order_id: str
    payment_id: str

class RzpRefundRequest(BaseModel):
    payment_id: str
    amount: int
    return_reason: str
    # Optional real feature overrides (for direct scoring panel)
    return_rate_90d: Optional[float] = None
    orders_last_90d: Optional[int] = None
    item_value_percentile: Optional[float] = None
    promo_code_used: Optional[int] = None
    account_age_days: Optional[int] = None
    order_to_return_days: Optional[float] = None
    same_day_reorder_after_return: Optional[int] = None

# --- ENDPOINTS ---

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": app.version,
        "model": "XGBoost Hybrid",
        "threshold": OPTIMAL_THRESHOLD,
        "features_count": len(FEATURE_COLS)
    }

@app.get("/metrics")
def get_metrics():
    try:
        with open("models/metrics.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Metrics not found")

@app.get("/threshold-explore")
def get_threshold_curve():
    try:
        with open("models/threshold_curve.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Threshold curve not found")

@app.post("/score")
def score_refund(data: ScoringFeatureInput):
    # 1. Convert input to dict matching feature columns
    input_dict = data.dict()
    
    # 2. Rule Layer
    triggered, rule_name, band = apply_rules(input_dict)
    
    score = 1.0 if triggered else 0.0
    reason = f"Rule Triggered: {rule_name}" if triggered else ""
    shap_out = []
    
    # 3. ML Layer (if rules didn't catch it)
    if not triggered:
        # Build dataframe for XGBoost
        df_inf = pd.DataFrame([{col: input_dict.get(col, 0) for col in FEATURE_COLS}])
        
        # Predict
        score = float(model.predict_proba(df_inf)[0, 1])
        band = "High" if score >= OPTIMAL_THRESHOLD else ("Medium" if score >= OPTIMAL_THRESHOLD * 0.5 else "Low")
        
        # SHAP Explanation
        sv = explainer.shap_values(df_inf)[0]
        
        # Format SHAP for frontend (top 3)
        top_indices = np.argsort(np.abs(sv))[-3:][::-1]
        for i in top_indices:
            feat = FEATURE_COLS[i]
            val = df_inf.iloc[0][feat]
            contrib = float(sv[i])
            shap_out.append({"feature": feat, "value": val, "contribution": contrib})
            
        reason = f"ML Model Score: {score:.2f}"
    
    # Trigger Webhook if High Risk
    if band == "High":
        trigger_webhook_alert(data.order_id, data.refund_id or "N/A", score, reason)
        
    # 4. Audit Log
    conn = get_db()
    conn.execute("""
        INSERT INTO audit_log (order_id, refund_id, score, band, triggered_by, reason, shap_values, threshold, features_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.order_id,
        data.refund_id,
        score,
        band,
        "Rule" if triggered else "XGBoost",
        reason,
        json.dumps(shap_out),
        OPTIMAL_THRESHOLD,
        json.dumps(input_dict)
    ))
    conn.commit()
    conn.close()
    
    return {
        "order_id": data.order_id,
        "score": score,
        "risk_band": band,
        "threshold_used": OPTIMAL_THRESHOLD,
        "explanation": shap_out,
        "triggered_by": "Rule" if triggered else "XGBoost",
        "reason_summary": reason
    }

@app.get("/audit")
def get_audit_logs(limit: int = 50, band: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM audit_log"
    params = []
    
    if band:
        query += " WHERE band = ?"
        params.append(band)
        
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- RAZORPAY MOCK ENDPOINTS FOR LIVE DEMO ---

@app.post("/razorpay/create-order")
def rzp_create_order(req: RzpOrderRequest):
    if not USE_MOCK_RZP:
        order = rzp_client.order.create({
            "amount": req.amount,
            "currency": "INR",
            "notes": {
                "category": req.category,
                "product_name": req.product_name,
                "promo_code": req.promo_code or ""
            }
        })
        return order
    else:
        # MOCK
        import uuid
        return {
            "id": f"order_{uuid.uuid4().hex[:14]}",
            "amount": req.amount,
            "currency": "INR",
            "status": "created",
            "notes": {"category": req.category, "product_name": req.product_name, "promo_code": req.promo_code}
        }

@app.post("/razorpay/verify-payment")
def rzp_verify_payment(req: RzpPaymentRequest):
    # In a real app, we'd verify signature. Here we just mock capture.
    return {"status": "captured", "payment_id": req.payment_id, "order_id": req.order_id}

@app.post("/razorpay/request-refund")
def rzp_request_refund(req: RzpRefundRequest):
    import uuid
    refund_id = f"rfnd_{uuid.uuid4().hex[:14]}"
    
    if not USE_MOCK_RZP:
        try:
            refund = rzp_client.refund.create({
                "payment_id": req.payment_id,
                "amount": req.amount,
                "notes": {"return_reason": req.return_reason}
            })
            refund_id = refund["id"]
        except Exception as e:
            # We hit this because the frontend sends 'pay_mock123'
            # We can't programmatically generate real payments in Razorpay without a frontend checkout.
            print(f"WARNING: Razorpay API Error (Using mock refund ID to continue): {str(e)}")

    # We need to score this refund!
    # In a real system, we'd fetch the customer's history from our DB to build the features.
    # For the hackathon demo, we'll synthesize the historical features based on the reason 
    # to show the model reacting to different inputs live.
    
    # If they pick "changed_mind", we simulate a wardrober profile (fast return, high amount)
    # If they pick "damaged", we simulate a normal profile.
    
    # If real features were passed, use them instead of the hardcoded simulation
    if req.return_rate_90d is not None:
        # Real features provided — use them directly
        reason_map = {
            "changed_mind": {"return_reason_changed_mind": 1},
            "damaged": {"return_reason_damaged": 1},
            "wrong_size": {"return_reason_wrong_size": 1},
            "not_as_described": {"return_reason_not_as_described": 1},
            "no_reason": {"return_reason_no_reason": 1},
        }
        reason_ohe = reason_map.get(req.return_reason, {"return_reason_nan": 1})
        features = ScoringFeatureInput(
            order_id=req.payment_id.replace("pay_mock_", "order_") if req.payment_id.startswith("pay_mock_") else f"order_{req.payment_id[:6]}",
            refund_id=refund_id,
            return_rate_90d=req.return_rate_90d,
            orders_last_90d=req.orders_last_90d or 5,
            item_value_percentile=req.item_value_percentile or 0.5,
            promo_code_used=req.promo_code_used or 0,
            account_age_days=req.account_age_days or 365,
            order_to_return_days=req.order_to_return_days or 7.0,
            same_day_reorder_after_return=req.same_day_reorder_after_return or 0,
            **reason_ohe
        )
        score_result = score_refund(features)
        return {"refund_id": refund_id, "payment_id": req.payment_id, "status": "processed", "recidian_assessment": score_result}

    is_wardrober_sim = (req.return_reason == "changed_mind" and req.amount > 100000)
    
    features = ScoringFeatureInput(
        order_id="order_demo",
        refund_id=refund_id,
        return_rate_90d=0.8 if is_wardrober_sim else 0.1,
        orders_last_90d=5,
        item_value_percentile=0.9 if is_wardrober_sim else 0.4,
        promo_code_used=0,
        account_age_days=45 if is_wardrober_sim else 365,
        address_mismatch_flag=0,
        order_to_return_days=2.0 if is_wardrober_sim else 14.0,
        same_day_reorder_after_return=0,
        return_reason_changed_mind=1 if req.return_reason == "changed_mind" else 0,
        return_reason_damaged=1 if req.return_reason == "damaged" else 0,
        return_reason_not_as_described=1 if req.return_reason == "not_as_described" else 0,
        return_reason_wrong_size=1 if req.return_reason == "wrong_size" else 0
    )
    
    score_result = score_refund(features)
    
    return {
        "refund_id": refund_id,
        "payment_id": req.payment_id,
        "status": "processed",
        "recidian_assessment": score_result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
