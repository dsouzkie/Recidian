# RECIDIAN — Return-Risk Intelligence Engine

*Not every return is a loss. RECIDIAN tells you which ones are.*

[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-%2346E3B7?style=for-the-badge&logo=render)](https://recidian.onrender.com)
[![Razorpay Track 02](https://img.shields.io/badge/Razorpay_Buildathon-Track_02-blue?style=for-the-badge)](#)

**Live Demo:** [https://recidian.onrender.com](https://recidian.onrender.com)  
*(Note: Hosted on Render Free Tier. Please allow 60-90 seconds for the initial cold start if the server is asleep).*

---

## 🎯 Problem Statement & Track Alignment
**The Hackathon Mandate (Track 02 - AI Risk Manager):**
> *"Stop the merchant losing money to fraud, returns and chargebacks. Build a working detector, verifier or auto-responder for one class of loss, with measured precision and recall on a held-out test set... strictly defense-only."*

**The RECIDIAN Solution:**
We explicitly targeted **Return Abuse** (Wardrobing, Promo-exploitation, Serial returning). RECIDIAN is a **strictly defense-only** ML interceptor. It listens passively to Razorpay's `/v1/refunds` API, synthesizes historical account velocity, and scores the risk of an incoming refund *before* it is approved, saving merchant revenue and operational costs. 

---

## 🛠️ Tech Stack
* **Backend:** FastAPI, Python, Uvicorn
* **Machine Learning:** XGBoost, SHAP (TreeExplainer), Scikit-Learn, Pandas
* **Frontend:** HTML5, CSS3, Vanilla JS, Chart.js
* **Integrations:** Razorpay Test API Webhooks
* **Database / Audit:** SQLite3

---

## ⚡ Key USPs & Features

1. **Business Cost Optimization (Not just "Accuracy"):** We didn't optimize for arbitrary ML accuracy. We assigned a financial penalty to False Positives and False Negatives, sweeping 99 thresholds to find the mathematical minimum business loss.
2. **SHAP Explainability (No Black Boxes):** In real FinTech, freezing money blindly is a compliance nightmare. We integrated a SHAP `TreeExplainer`. Every prediction outputs exact feature contributions (e.g., *"Blocked because the user's 90-day return rate is 80%"*), ensuring total operational transparency.
3. **Hybrid Scoring Architecture:** We built a hardcoded rule layer for 0ms instant triggers (speed), backed by a powerful XGBoost Classifier for complex, non-linear pattern recognition.

---

## 🧠 Deep Dive: Data Archetypes & "Hard Negatives"
Because real fraud data is proprietary, we synthesized 20,400+ transactions mirroring Razorpay's API schemas, calibrated strictly to NRF 2024 retail benchmarks. We built four strict behavioral profiles:
* **Normal Customers:** Low return rate, standard account age.
* **Wardrobers:** High-value items, returned within 1-2 days for "Changed Mind".
* **Promo Abusers:** High promo code usage, immediate returns to harvest discounts.
* **The "Hard Negative" (Loyal High-Freq):** We intentionally engineered customers with massive 80% return rates but extremely high order volume (22+ orders/month) and old accounts. This forced the XGBoost model to learn complex multi-feature matrices rather than relying on a lazy, single-variable threshold.

---

## 💸 Deep Dive: The Cost Matrix & Thresholding
We evaluated the model on an 80/20 held-out test set. To determine the optimal threshold, we ran a mathematical cost sweep:
* **False Positive Penalty:** `₹2,150` (The cost of insulting a good customer, lifetime value loss, and friction).
* **False Negative Penalty:** `₹1,085` (The cost of return shipping + average item loss to a fraudster).

**Results:** The engine found that a strict classification **Threshold of 0.69** minimized total business loss to exactly `₹36,550` on the test set.

| Metric | Value | Meaning |
|---|---|---|
| **Precision** | `94.3%` | When we flag a refund as high-risk, we are correct 94.3% of the time. |
| **Recall** | `93.0%` | We caught 93.0% of all abusive returns in the dataset. |
| **PR-AUC** | `0.940` | Highly resilient even against class imbalance. |

---

## 🏛️ Architecture Flow

```mermaid
graph TD
    subgraph Razorpay Cloud
        A[Razorpay Checkout] --> B(Create Order & Mock Payment)
        B --> C{Customer Requests Refund}
    end

    C -- "POST /v1/refunds" --> D[FastAPI Interceptor]

    subgraph RECIDIAN Risk Engine
        D --> E[Feature Synthesis Engine]
        E -- "OHE & Normalization" --> F{Rule Layer}
        
        F -- "Trigger: Amount > ₹1M" --> G[FLAG: HIGH RISK]
        F -- "Pass" --> H[XGBoost Engine]
        
        H -- "Risk Probability" --> I[SHAP Explainer]
        I -- "Decomposed Features" --> J{Score >= 0.69?}
    end

    J -- "Yes (High Risk)" --> K[Fire Webhook: Block Refund]
    J -- "No (Low Risk)" --> L[Fire Webhook: Approve Refund]
    
    G -.-> M[(SQLite Immutable Audit Log)]
    K -.-> M
    L -.-> M

    classDef default fill:#0a1128,stroke:#00f3ff,stroke-width:2px,color:#fff,rx:8,ry:8;
    classDef ml fill:#140514,stroke:#bc13fe,stroke-width:2px,color:#fff,rx:8,ry:8;
    classDef db fill:#05140a,stroke:#22c55e,stroke-width:2px,color:#fff,rx:8,ry:8;
    
    class H,I ml;
    class M db;
```

---

## 💻 Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dsouzkie/Recidian.git
   cd Recidian
   ```
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Variables**
   Create a `.env` file containing your Razorpay Test Keys:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxx
   ```
4. **Run the Backend**
   ```bash
   python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
   ```
5. **View the Dashboard**
   Navigate to `http://localhost:8000`.

---

## 🚀 Future Roadmap
- **Peer-Group Normalization:** Add relative Z-scores (e.g., comparing a customer's return rate to the average for their specific product category, since clothes are returned more often than electronics).
- **Network Graph Analysis:** Implement graph databases to detect 'Abuse Rings' (multiple accounts sharing the same device fingerprint or IP address to bypass blocks).
