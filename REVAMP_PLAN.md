# RECIDIAN — Revamp Implementation Plan v2.0
### Phase: POST-HACKATHON REVAMP | Created: 2026-09-02 | Deadline: 2026-09-05
### Author: AI Agent (Antigravity) | Project: Razorpay AI Buildathon, Track 02

---

## ⚡ AGENT RESUME PROMPT (Copy this when starting a new session)

```
I am working on RECIDIAN, a Razorpay AI Buildathon Track 02 submission.
It is a defense-only ML risk scorer that intercepts Razorpay refunds.
The codebase is at: c:\Users\chris\Downloads\razorpay\
The GitHub repo is: https://github.com/dsouzkie/Recidian
The live deployment is: https://recidian.onrender.com

CURRENT PHASE: Revamp — adding real scoring panel, threshold chart, limitations card.
READ THESE FILES IN ORDER BEFORE DOING ANYTHING:
1. REVAMP_PLAN.md — the implementation plan (what to build, what NOT to touch)
2. REVAMP_TRACKER.md — the living log (what's done, what's in progress, what broke)
3. src/app.py — the FastAPI backend (understand what endpoints exist)
4. static/index.html — the frontend (understand current layout before adding)

HARD RULES:
- NEVER modify src/generate_data.py, src/features.py, src/rules.py, src/train_model.py, src/evaluate.py
- NEVER retrain the model or regenerate data
- NEVER modify models/ or data/ directories
- NEVER modify Dockerfile or requirements.txt
- ALL changes are additive to static/index.html and static/portfolio.html only
- ALWAYS update REVAMP_TRACKER.md after every task
- The Razorpay test mode stays. Do NOT attempt real payment gateway integration.

The /score endpoint (POST) already exists and works. The problem is the frontend never calls it.
The fix is purely frontend — adding a real scoring panel to static/index.html.
```

---

## 📋 Context: The Whole Truth

### What We Told the World vs. What's Actually True

| Claim | Reality |
|---|---|
| "Live Razorpay Integration" | ✅ TRUE — real `order_` IDs created via Razorpay Test API |
| "ML model scores each refund" | ⚠️ PARTIALLY TRUE — model exists and works, but demo bypasses it |
| "SHAP explainability" | ✅ TRUE — real SHAP TreeExplainer, values are real |
| "94.3% Precision on held-out test set" | ✅ TRUE — real evaluation on 20% held-out data |
| "Threshold 0.69 mathematically derived" | ✅ TRUE — 100-point cost sweep |
| "Interactive Live Demo" | ❌ SCRIPTED — dropdown maps to 2 hardcoded profiles |

### The Smoking Gun (app.py Lines 312-329)
```python
# The entire "live" demo reduces to this:
is_wardrober_sim = (req.return_reason == "changed_mind" and req.amount > 100000)
features = ScoringFeatureInput(
    return_rate_90d=0.8 if is_wardrober_sim else 0.1,  # ALWAYS one of two values
    account_age_days=45 if is_wardrober_sim else 365,   # ALWAYS one of two values
)
```
This is theater. Priority 1 fixes this.

### Why the Real Dataset Question is Closed
There is no publicly available labeled "return abuse" dataset. Options:
- **Credit card fraud datasets (Kaggle):** Wrong problem. Different features (V1-V28 PCA components, not return behavioral features).
- **Raw e-commerce return datasets:** No abuse labels. Would require expensive hand-labeling.
- **KNN augmentation:** Only useful when you have real unlabeled data with missing fields. We have fully-labeled, fully-featured synthetic data. KNN adds complexity with zero benefit.

**Decision: Keep synthetic. Add calibration note.** Distributions are validated against NRF 2024 benchmarks (fashion 28-35% returns, electronics 7-12%). Our wardrober archetype (40-70%) matches documented wardrobing patterns.

### Why Real Razorpay Gateway is NOT Being Added
- Real gateway requires KYC-verified merchant + actual INR movement
- Test mode already creates real Razorpay order IDs (verifiable in their dashboard)
- Judges care about ML architecture, not whether money moved
- Risk: weeks of KYC compliance for zero judge value
- Decision: Test mode stays.

---

## 🔒 Frozen Files (DO NOT TOUCH UNDER ANY CIRCUMSTANCES)

```
src/generate_data.py    — data complete
src/features.py         — features complete  
src/rules.py            — rules complete
src/train_model.py      — model trained
src/evaluate.py         — metrics locked
models/model.json       — trained weights
models/shap_explainer.pkl
models/metrics.json
models/threshold.json   — threshold = 0.69
models/threshold_curve.json  — 99-point cost curve (DATA EXISTS, not yet visualized)
models/feature_columns.json
data/ (all CSVs)
static/confusion_matrix.png
static/roc_curve.png
static/pr_curve.png
static/shap_summary.png
Dockerfile
requirements.txt
```

---

## ✅ What Already Works (Confirmed by Live Test on 2026-09-01)

1. `POST /razorpay/create-order` → Creates real Razorpay test order, returns `order_XXX` ID
2. `POST /razorpay/verify-payment` → Mock capture, returns payment status
3. `POST /razorpay/request-refund` → Creates mock `rfnd_XXX` ID, runs **scripted** scoring (the bug)
4. `POST /score` → **REAL ENDPOINT** — Takes `ScoringFeatureInput`, runs Rules + XGBoost + SHAP, logs to SQLite. Frontend never calls this.
5. `GET /metrics` → Returns `models/metrics.json`
6. `GET /threshold-explore` → Returns `models/threshold_curve.json` (99 data points)
7. `GET /audit` → Returns SQLite audit log rows
8. `GET /health` → Returns model status
9. `GET /` → Redirects to `/static/index.html`

---

## 🎯 Priorities

---

### PRIORITY 1 — Real Scoring Panel
**Status:** NOT STARTED  
**Files:** `static/index.html` ONLY (additive)  
**Time estimate:** 3 hours  
**Endpoint used:** `POST /score` (already exists)

**What to build:**
A new dashboard card titled `"Score Engine — Direct Risk Assessment"` with:

**Input controls:**
```
return_rate_90d          → Slider 0.0–1.0, step 0.01, default 0.10
orders_last_90d          → Number input, default 5
item_value_percentile    → Slider 0.0–1.0, step 0.01, default 0.50
promo_code_used          → Toggle (0/1), default off
account_age_days         → Number input, default 365
order_to_return_days     → Number input, default 7
same_day_reorder         → Toggle (0/1), default off
return_reason            → Dropdown: changed_mind, damaged, wrong_size, not_as_described, no_reason
```

**Three scenario buttons (CRITICAL for demo):**
```javascript
// Normal Customer — should score LOW
{ return_rate_90d: 0.08, orders_last_90d: 4, item_value_percentile: 0.4,
  promo_code_used: 0, account_age_days: 400, order_to_return_days: 12,
  same_day_reorder_after_return: 0, return_reason: "damaged" }

// Wardrober — should score HIGH (>90%)
{ return_rate_90d: 0.75, orders_last_90d: 5, item_value_percentile: 0.95,
  promo_code_used: 0, account_age_days: 45, order_to_return_days: 2,
  same_day_reorder_after_return: 0, return_reason: "changed_mind" }

// Loyal High-Frequency (THE KILLER DEMO MOMENT — scores LOW despite 80% return rate)
{ return_rate_90d: 0.80, orders_last_90d: 22, item_value_percentile: 0.6,
  promo_code_used: 1, account_age_days: 730, order_to_return_days: 8,
  same_day_reorder_after_return: 1, return_reason: "wrong_size" }
```

**Request payload structure (matching ScoringFeatureInput exactly):**
```json
{
  "order_id": "order_direct_score",
  "return_rate_90d": 0.75,
  "orders_last_90d": 5,
  "item_value_percentile": 0.95,
  "promo_code_used": 0,
  "account_age_days": 45,
  "address_mismatch_flag": 0,
  "order_to_return_days": 2.0,
  "same_day_reorder_after_return": 0,
  "category_return_rate_deviation": 0.0,
  "return_reason_changed_mind": 1,
  "return_reason_damaged": 0,
  "return_reason_no_reason": 0,
  "return_reason_not_as_described": 0,
  "return_reason_wrong_size": 0,
  "return_reason_nan": 0
}
```

**Output:** Reuse existing risk gauge + SHAP list components from the Razorpay demo.

**Verification test:**
- Loyal HF profile MUST score < 50% despite `return_rate_90d: 0.80`
- If it scores > 80% the ML is just thresholding on one feature (bad)
- Changing `order_to_return_days` from 2 → 30 must change the score (proves live ML)

---

### PRIORITY 2 — Threshold Cost Curve Chart
**Status:** NOT STARTED  
**Files:** `static/index.html` ONLY (additive)  
**Time estimate:** 1 hour  
**Endpoint used:** `GET /threshold-explore` (already exists, returns 99-point JSON)

**Chart.js config:**
```javascript
// Fetch from /threshold-explore
// Data format: [{threshold: 0.01, total_cost: X, fp_cost: Y, fn_cost: Z}, ...]
// Line 1: total_cost (primary, blue)
// Line 2: fp_cost (dashed red)
// Line 3: fn_cost (dashed orange)
// Special: annotation at threshold=0.69 with label "Optimal — INR 36,550"
```

**Why this matters:** Fraud Spine Director disclosed their cost ratio in text. We visualize ours interactively. No competitor in the research brief did this.

---

### PRIORITY 3 — Honest Limitations Card
**Status:** NOT STARTED  
**Files:** `static/index.html` ONLY (additive)  
**Time estimate:** 30 mins

**Three cards:**

**Card 1 — What's Simulated:**
> The Razorpay demo uses `pay_mock123` as payment ID because programmatic card capture requires a client-side checkout UI with real card entry. All Order IDs (e.g. `order_TWprJiPLrXJE4B`) are genuine Razorpay test-mode API calls. ML scoring is 100% real.

**Card 2 — Dataset Calibration:**
> Synthetic distributions validated against NRF 2024 benchmarks: fashion returns 28-35%, electronics 7-12%. Wardrober archetype (40-70% return rate) matches documented wardrobing behavior. The Loyal High-Frequency hard negative was explicitly designed to prevent trivial threshold-based separation.

**Card 3 — What's Next:**
> Peer-Group Normalization (Z-score vs. category baseline). Device Graph abuse-ring detection. Rolling burst detection (refund spike vs. 6-hour rolling baseline).

---

### PRIORITY 4 — Push & Redeploy
**Status:** NOT STARTED  
**Time estimate:** 15 mins

```bash
git add static/index.html static/portfolio.html README.md REVAMP_PLAN.md REVAMP_TRACKER.md
git commit -m "feat: real scoring panel, threshold chart, limitations disclosure"
git push origin main
# Render auto-deploys on push
```

---

### PRIORITY 5 — Record Demo Video (USER TASK)
**Status:** NOT STARTED  
**Time estimate:** 1 hour

**Script:**
1. **(0:00-0:30)** Open dashboard. Read track quote from hero. "We built RECIDIAN — a defense-only return-risk scorer for Razorpay merchants."
2. **(0:30-1:30)** Scoring panel → Click "Loyal High-Frequency". Score LOW despite 80% return rate. Say: "This is the hardest thing to get right. The model learned that 80% returns is fine if you order 22 times a month. We had to explicitly design this as a hard negative in our dataset to force the model to use multi-feature patterns."
3. **(1:30-2:30)** Click "Wardrober". Score hits 99%+. Point to SHAP. Say: "Every blocked refund comes with a mathematically rigorous, auditable explanation."
4. **(2:30-3:30)** Scroll to Threshold Chart. Point to 0.69 marker. Say: "We didn't pick this threshold — we calculated it. We swept 100 thresholds, assigned INR 2,000 to each missed fraud and INR 500 to each false positive, and found the exact point where total business loss is minimized."
5. **(3:30-4:00)** Run Razorpay demo. Show real `order_` ID. Say: "This is a genuine Razorpay test-mode API call."
6. **(4:00-4:30)** Show Audit Log with real entries.
7. **(4:30-5:00)** Show Limitations card. Say: "We know exactly what's simulated. Here's what we'd build next with more time."

---

## 📋 Files Modified in This Phase

| File | Type | What Changes |
|---|---|---|
| `static/index.html` | ADDITIVE | Scoring panel + threshold chart + limitations card |
| `static/portfolio.html` | ADDITIVE | Calibration note in Module 02 |
| `README.md` | ADDITIVE | Dataset calibration paragraph |
| `REVAMP_PLAN.md` | NEW | This file |
| `REVAMP_TRACKER.md` | NEW | Living log for revamp phase |

**Files that will NOT change:** Everything in `src/`, `models/`, `data/`, `Dockerfile`, `requirements.txt`
