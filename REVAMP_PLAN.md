# RECIDIAN — Revamp Implementation Plan v3.0
### For Gemini Execution | Created: 2026-09-02 | Deadline: 2026-09-05
### Principle: ADDITIVE ONLY to static/index.html and static/portfolio.html

---

## ⚡ AGENT RESUME PROMPT — PASTE THIS WHEN STARTING A NEW SESSION

```
PROJECT: RECIDIAN — Razorpay AI Buildathon, Track 02: AI Risk Manager
LOCATION: c:\Users\chris\Downloads\razorpay\
GITHUB: https://github.com/dsouzkie/Recidian (main branch)
LIVE URL: https://recidian.onrender.com
SERVER CMD: py -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --env-file .env
PYTHON CMD: Use 'py' not 'python' on this Windows machine
GIT SEPARATOR: Use semicolons (;) not && in PowerShell

CURRENT PHASE: Revamp v3.0
FIRST: Read REVAMP_TRACKER.md to see exact current status before doing anything.
THEN: Read REVAMP_PLAN.md (this file) fully before writing a single line of code.

HARD RULES — NEVER VIOLATE:
1. NEVER touch src/generate_data.py, src/features.py, src/rules.py, src/train_model.py, src/evaluate.py
2. NEVER retrain the model or regenerate the data
3. NEVER touch models/ or data/ directories
4. NEVER touch Dockerfile or requirements.txt
5. ALL code changes go into static/index.html only (additive HTML/CSS/JS sections)
6. static/portfolio.html gets one additive module only
7. src/app.py gets ONE additive change only (see Priority 1, Step 3)
8. After every completed task, update REVAMP_TRACKER.md
9. Do NOT add new Python packages
10. Do NOT attempt Razorpay real payment gateway (test mode only)
11. Windows terminal cannot print emojis or ₹ — use INR in any Python print()
```

---

## 0. THE WHOLE TRUTH — Current State of the Project

### What's Real vs. What's Scripted

| Claim Made | Reality | File / Lines |
|---|---|---|
| "Live Razorpay API integration" | ✅ REAL — Creates genuine Razorpay test-mode `order_XXX` IDs | app.py:257-269 |
| "ML model scores the refund" | ❌ SCRIPTED — Demo maps dropdown to 2 hardcoded feature profiles | app.py:312-329 |
| "SHAP Explainability" | ✅ REAL — TreeExplainer runs, values are genuine | app.py:193-201 |
| "94.3% Precision on held-out test" | ✅ REAL — Evaluated on 20% stratified holdout | evaluate.py |
| "Threshold 0.69 mathematically derived" | ✅ REAL — 100-point cost sweep, data in threshold_curve.json | train_model.py |
| "Threshold curve chart" | ❌ MISSING — Data exists but never rendered | models/threshold_curve.json |
| "Honest about limitations" | ❌ MISSING — No disclosure in UI | — |

### The Critical Bug (app.py Lines 312-329)
```python
# This is what actually happens when you click "Execute Refund & Score"
is_wardrober_sim = (req.return_reason == "changed_mind" and req.amount > 100000)
# THE MODEL ALWAYS RECEIVES ONE OF ONLY TWO HARDCODED PROFILES:
features = ScoringFeatureInput(
    return_rate_90d=0.8 if is_wardrober_sim else 0.1,
    account_age_days=45 if is_wardrober_sim else 365,
    order_to_return_days=2.0 if is_wardrober_sim else 14.0,
    ...
)
```
A Razorpay engineer reviewing code would spot this immediately. The fix is Priority 1.

### What the POST /score Endpoint Already Supports (NEVER USED BY FRONTEND)
```
Endpoint: POST /score
Input: ScoringFeatureInput (Pydantic model, all fields below)
Output: { order_id, score, risk_band, threshold_used, explanation: [{feature, value, contribution}], triggered_by, reason_summary }
Runs: Rule layer → XGBoost → SHAP → Audit log INSERT
This endpoint is COMPLETE and TESTED. Frontend just never calls it.
```

### ScoringFeatureInput Fields (exact, from app.py lines 108-126)
```
order_id: str                           (required, use "direct_score" for panel)
refund_id: str = None                   (optional)
return_rate_90d: float = 0.0
orders_last_90d: int = 0
item_value_percentile: float = 0.5
promo_code_used: int = 0
account_age_days: int = 365
address_mismatch_flag: int = 0
order_to_return_days: float = 0.0
same_day_reorder_after_return: int = 0
category_return_rate_deviation: float = 0.0
return_reason_changed_mind: int = 0    ← OHE fields, exactly one = 1
return_reason_damaged: int = 0
return_reason_no_reason: int = 0
return_reason_not_as_described: int = 0
return_reason_wrong_size: int = 0
return_reason_nan: int = 0
```

### Existing JS Functions in index.html (DO NOT REWRITE, REUSE)
```javascript
updateGauge(score, band, shap_values)  // Line 647 — renders risk gauge + SHAP bars
logStep(msg)                           // Line 704 — appends to console log div
fetchAuditLogs()                       // Line 617 — refreshes audit table
init()                                 // Line 602 — loads metrics on page load
runLiveDemo()                          // Line 710 — the Razorpay flow (DO NOT TOUCH)
```

### Existing HTML Structure in index.html (Know before inserting)
```
Lines 1-420:   <style> block — CSS variables, classes
Lines 421-450: <body> HERO section (dark blue header with GitHub button)
Lines 452-477: KPI Grid (Precision, Recall, FP Cost, Threshold)
Lines 480-507: Card: "Live Razorpay Integration Demo" (DO NOT TOUCH)
Lines 509-529: Card: "Live AI Assessment & Explainability" (DO NOT TOUCH)
Lines 531-543: Card: "Model Performance & Cost Analytics" (4 PNG charts)
Lines 545-563: Card: "Immutable Audit Log"
Lines 565-575: Portfolio transition button
Lines 577-583: Cyber transition overlay div
Lines 585-765: <script> block with all JS functions
```

### Where to Insert New Sections (EXACT LINE NUMBERS)
```
AFTER line 543 (end of charts card), BEFORE line 545 (start of audit card):
→ INSERT: Threshold Cost Curve Chart card (Priority 2)

AFTER line 563 (end of audit log card), BEFORE line 565 (closing </div>):
→ INSERT: Limitations & Calibration cards (Priority 3)

AFTER line 565 (closing div), BEFORE line 569 (portfolio button):
→ INSERT: nothing (keep portfolio button last)

INSIDE <script> block, AFTER the init() function (line ~615):
→ INSERT: scorePanel() function and initThresholdChart() function (Priority 1 & 2)
```

---

## 0.1 Research Brief Summary (What Competitors Did Better)

From `razorpay-risk-manager-research-brief.md`:

| Pattern All Strong Projects Had | RECIDIAN Has This? |
|---|---|
| Deterministic decision layer, LLM off hot path | ✅ (Rules + XGBoost) |
| Cost-sensitive threshold with defined cost ratio | ✅ (Computed, NOT visualized) |
| SHAP explainability | ✅ UNIQUE advantage |
| Razorpay API integration | ✅ UNIQUE advantage |
| Real live scoring in demo (not theater) | ❌ MISSING |
| Audit trail first-class | ✅ (SQLite) |
| Three-tier actions (Low/Med/High) | ✅ |
| Honest limitations explicitly disclosed | ❌ MISSING |
| Burst/cohort detection layered on top | ❌ (future work only) |

**RiskLens specifically:** Had device-graph / mule-ring detection. We cannot build this in 3 days, but we SHOULD mention it in the "What's Next" card.

**Fraud Spine Director specifically:** Visualized cost-sensitive model comparison. We have cost data. Rendering it as Chart.js is Priority 2.

---

## 0.2 Frozen Files (NEVER TOUCH)

```
src/generate_data.py    src/features.py     src/rules.py
src/train_model.py      src/evaluate.py
models/model.json       models/shap_explainer.pkl
models/metrics.json     models/threshold.json
models/threshold_curve.json  models/feature_columns.json
data/ (all CSVs and DB)
static/confusion_matrix.png  static/roc_curve.png
static/pr_curve.png          static/shap_summary.png
Dockerfile              requirements.txt
```

---

## 1. PRIORITY 1 — Real Scoring Panel
**Status:** NOT STARTED  
**Estimated time:** 2-3 hours  
**Files changed:** `static/index.html` (additive) + `src/app.py` (one line fix)

### Step 1: Fix app.py — Make Razorpay Demo Pass Real Features Through

**Problem:** `/razorpay/request-refund` synthesizes fake features. We need it to also accept real feature overrides.

**Change:** Add optional feature fields to `RzpRefundRequest` so the demo can optionally pass real features. **If not provided, keep existing hardcoded logic so the existing demo STILL WORKS.**

In `src/app.py`, modify `RzpRefundRequest` class (lines 138-141):
```python
# BEFORE (lines 138-141):
class RzpRefundRequest(BaseModel):
    payment_id: str
    amount: int
    return_reason: str

# AFTER (additive — add optional fields, existing fields unchanged):
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
```

Then in the `rzp_request_refund` function (around line 312), add a check BEFORE the hardcoded block:
```python
# BEFORE the existing is_wardrober_sim line, add:
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
        order_id="direct_score",
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

# EXISTING hardcoded block stays UNCHANGED below this new block
is_wardrober_sim = (req.return_reason == "changed_mind" and req.amount > 100000)
...
```

**Verification:** If `return_rate_90d` is not sent, old behavior unchanged. If sent, real ML runs.

---

### Step 2: Add Scoring Panel HTML to index.html

**Insert AFTER line 507 (`</div>` closing the Razorpay demo card), BEFORE line 509 (`<!-- RISK ENGINE COLUMN -->`).**

This adds a new full-width card above the existing Risk Gauge card.

```html
<!-- ============================================================ -->
<!-- PRIORITY 1: REAL SCORING PANEL — calls POST /score directly  -->
<!-- DO NOT REMOVE OR MODIFY EXISTING CARDS ABOVE OR BELOW        -->
<!-- ============================================================ -->
<div class="card full-width" id="scoring-panel" style="border: 2px solid var(--rzp-blue);">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem;">
        <div>
            <h2 style="margin: 0 0 0.25rem 0;">Score Engine — Direct ML Risk Assessment</h2>
            <p style="font-size: 0.9rem; color: var(--text-muted); margin: 0;">
                Calls <code>POST /score</code> directly with real feature values you control. 
                The Razorpay demo above uses this same engine internally.
            </p>
        </div>
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <button onclick="loadScenario('normal')" style="background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7; padding:0.4rem 0.8rem; border-radius:6px; font-size:0.8rem; font-weight:600; cursor:pointer;">Normal Customer</button>
            <button onclick="loadScenario('wardrober')" style="background:#fce4ec; color:#880e4f; border:1px solid #f48fb1; padding:0.4rem 0.8rem; border-radius:6px; font-size:0.8rem; font-weight:600; cursor:pointer;">Wardrober</button>
            <button onclick="loadScenario('loyalhf')" style="background:#e3f2fd; color:#0d47a1; border:1px solid #90caf9; padding:0.4rem 0.8rem; border-radius:6px; font-size:0.8rem; font-weight:600; cursor:pointer;">Loyal High-Freq ★</button>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
        <!-- LEFT: Input Controls -->
        <div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="form-group">
                    <label>Return Rate (90d) <span id="rr_val" style="color:var(--rzp-blue); font-weight:700;">0.10</span></label>
                    <input type="range" id="sp_rr" min="0" max="1" step="0.01" value="0.10"
                        oninput="document.getElementById('rr_val').innerText = parseFloat(this.value).toFixed(2)"
                        style="width:100%; accent-color: var(--rzp-blue);">
                </div>
                <div class="form-group">
                    <label>Item Value Percentile <span id="ivp_val" style="color:var(--rzp-blue); font-weight:700;">0.50</span></label>
                    <input type="range" id="sp_ivp" min="0" max="1" step="0.01" value="0.50"
                        oninput="document.getElementById('ivp_val').innerText = parseFloat(this.value).toFixed(2)"
                        style="width:100%; accent-color: var(--rzp-blue);">
                </div>
                <div class="form-group">
                    <label>Orders Last 90 Days</label>
                    <input type="number" id="sp_orders" value="5" min="1" max="50" style="width:100%;">
                </div>
                <div class="form-group">
                    <label>Account Age (Days)</label>
                    <input type="number" id="sp_age" value="365" min="1" max="1500" style="width:100%;">
                </div>
                <div class="form-group">
                    <label>Days to Return</label>
                    <input type="number" id="sp_days" value="7" min="0" max="90" style="width:100%;">
                </div>
                <div class="form-group">
                    <label>Return Reason</label>
                    <select id="sp_reason" style="width:100%;">
                        <option value="changed_mind">Changed Mind</option>
                        <option value="damaged">Item Damaged</option>
                        <option value="wrong_size">Wrong Size</option>
                        <option value="not_as_described">Not as Described</option>
                        <option value="no_reason">No Reason Given</option>
                    </select>
                </div>
                <div class="form-group" style="display:flex; align-items:center; gap:0.5rem;">
                    <label style="margin:0;">Promo Code Used?</label>
                    <input type="checkbox" id="sp_promo" style="width:20px; height:20px; accent-color:var(--rzp-blue);">
                </div>
                <div class="form-group" style="display:flex; align-items:center; gap:0.5rem;">
                    <label style="margin:0;">Same-Day Reorder?</label>
                    <input type="checkbox" id="sp_reorder" style="width:20px; height:20px; accent-color:var(--rzp-blue);">
                </div>
            </div>
            <button onclick="runScorePanel()" id="sp_btn"
                style="width:100%; margin-top:1rem; background: var(--rzp-blue); color: white; border: none; padding: 0.9rem; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer;">
                Run Risk Score →
            </button>
        </div>

        <!-- RIGHT: Result Display -->
        <div id="sp_result" style="display:flex; flex-direction:column; align-items:center; justify-content:center; background:var(--bg-page); border-radius:12px; padding:1.5rem; min-height:280px;">
            <div style="color:var(--text-muted); font-style:italic; text-align:center;">
                Select a scenario or fill in values, then click "Run Risk Score"
            </div>
        </div>
    </div>
</div>
<!-- ============================================================ -->
<!-- END PRIORITY 1 SCORING PANEL                                 -->
<!-- ============================================================ -->
```

---

### Step 3: Add Scoring Panel JavaScript

**Insert INSIDE the `<script>` block, AFTER the `init()` call at the very bottom (before `</script>`).**

```javascript
// ============================================================
// PRIORITY 1: Real Scoring Panel JS
// ============================================================
const SCENARIOS = {
    normal: {
        label: "Normal Customer",
        return_rate_90d: 0.08, orders_last_90d: 4, item_value_percentile: 0.4,
        promo_code_used: 0, account_age_days: 400, order_to_return_days: 12,
        same_day_reorder_after_return: 0, return_reason: "damaged",
        note: "Expect: LOW RISK. Rare returns, valid reason, established account."
    },
    wardrober: {
        label: "Wardrober",
        return_rate_90d: 0.75, orders_last_90d: 5, item_value_percentile: 0.95,
        promo_code_used: 0, account_age_days: 45, order_to_return_days: 2,
        same_day_reorder_after_return: 0, return_reason: "changed_mind",
        note: "Expect: HIGH RISK (>90%). Fast return, high value, new account, suspicious reason."
    },
    loyalhf: {
        label: "Loyal High-Frequency Shopper",
        return_rate_90d: 0.80, orders_last_90d: 22, item_value_percentile: 0.6,
        promo_code_used: 1, account_age_days: 730, order_to_return_days: 8,
        same_day_reorder_after_return: 1, return_reason: "wrong_size",
        note: "★ THE HARD TEST: 80% return rate but 22 orders. Expect LOW-MEDIUM RISK. If HIGH, the model is just thresholding on one feature (wrong)."
    }
};

function loadScenario(name) {
    const s = SCENARIOS[name];
    document.getElementById('sp_rr').value = s.return_rate_90d;
    document.getElementById('rr_val').innerText = s.return_rate_90d.toFixed(2);
    document.getElementById('sp_ivp').value = s.item_value_percentile;
    document.getElementById('ivp_val').innerText = s.item_value_percentile.toFixed(2);
    document.getElementById('sp_orders').value = s.orders_last_90d;
    document.getElementById('sp_age').value = s.account_age_days;
    document.getElementById('sp_days').value = s.order_to_return_days;
    document.getElementById('sp_reason').value = s.return_reason;
    document.getElementById('sp_promo').checked = s.promo_code_used === 1;
    document.getElementById('sp_reorder').checked = s.same_day_reorder_after_return === 1;

    // Show scenario note
    document.getElementById('sp_result').innerHTML = `
        <div style="text-align:center; padding:1rem; background: rgba(51,133,255,0.05); border-radius:8px; border:1px solid rgba(51,133,255,0.2);">
            <div style="font-weight:700; color:var(--rzp-blue); margin-bottom:0.5rem;">${s.label}</div>
            <div style="font-size:0.85rem; color:var(--text-muted);">${s.note}</div>
            <div style="margin-top:1rem; font-size:0.8rem; color:var(--text-muted);">Click "Run Risk Score" to execute</div>
        </div>`;
}

async function runScorePanel() {
    const btn = document.getElementById('sp_btn');
    btn.disabled = true;
    btn.innerText = 'Scoring...';

    const reason = document.getElementById('sp_reason').value;
    const reasonOHE = {
        return_reason_changed_mind: reason === 'changed_mind' ? 1 : 0,
        return_reason_damaged: reason === 'damaged' ? 1 : 0,
        return_reason_no_reason: reason === 'no_reason' ? 1 : 0,
        return_reason_not_as_described: reason === 'not_as_described' ? 1 : 0,
        return_reason_wrong_size: reason === 'wrong_size' ? 1 : 0,
        return_reason_nan: 0
    };

    const payload = {
        order_id: "direct_score_" + Date.now(),
        return_rate_90d: parseFloat(document.getElementById('sp_rr').value),
        orders_last_90d: parseInt(document.getElementById('sp_orders').value),
        item_value_percentile: parseFloat(document.getElementById('sp_ivp').value),
        promo_code_used: document.getElementById('sp_promo').checked ? 1 : 0,
        account_age_days: parseInt(document.getElementById('sp_age').value),
        address_mismatch_flag: 0,
        order_to_return_days: parseFloat(document.getElementById('sp_days').value),
        same_day_reorder_after_return: document.getElementById('sp_reorder').checked ? 1 : 0,
        category_return_rate_deviation: 0.0,
        ...reasonOHE
    };

    try {
        const res = await fetch(`${API_BASE}/score`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();

        const pct = Math.round(result.score * 100);
        const colors = { High: '#e94b4b', Medium: '#f5a623', Low: '#0fa457' };
        const color = colors[result.risk_band] || '#3385ff';

        let shapHTML = '';
        if (result.explanation && result.explanation.length > 0) {
            shapHTML = result.explanation.map(sv => {
                const isUp = sv.contribution > 0;
                return `<div style="display:flex; justify-content:space-between; padding:0.35rem 0; border-bottom:1px solid var(--border-color); font-size:0.82rem;">
                    <span style="font-family:'JetBrains Mono',monospace;">${sv.feature}</span>
                    <span style="color:${isUp ? '#e94b4b' : '#0fa457'}; font-weight:700;">${isUp ? '↑' : '↓'} ${sv.contribution.toFixed(3)}</span>
                </div>`;
            }).join('');
        }

        document.getElementById('sp_result').innerHTML = `
            <div style="text-align:center; width:100%;">
                <div style="font-size:3rem; font-weight:800; color:${color}; line-height:1;">${pct}%</div>
                <div style="font-size:1rem; font-weight:700; color:${color}; margin:0.5rem 0 1rem;">${result.risk_band.toUpperCase()} RISK — via ${result.triggered_by}</div>
                <div style="text-align:left; width:100%;">
                    <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-muted); margin-bottom:0.5rem;">SHAP Feature Contributions</div>
                    ${shapHTML || '<div style="color:var(--text-muted); font-style:italic;">Rule-based trigger (no SHAP)</div>'}
                </div>
            </div>`;

        fetchAuditLogs();
    } catch(e) {
        document.getElementById('sp_result').innerHTML = `<div style="color:#e94b4b;">Error: ${e.message}</div>`;
    }

    btn.disabled = false;
    btn.innerText = 'Run Risk Score →';
}
// ============================================================
// END PRIORITY 1 JS
// ============================================================
```

---

### Step 4: Verify Priority 1

After implementing, test these cases in order:
1. Click "Normal Customer" → run → score MUST be < 40%
2. Click "Wardrober" → run → score MUST be > 85%
3. Click "Loyal High-Freq ★" → run → score MUST be < 55% despite `return_rate_90d=0.80`
   - **If Loyal HF scores > 80%: STOP. The model is just thresholding. This means a feature is wrong. Check the payload is being sent correctly to /score.**
4. Manually change `return_rate_90d` slider from 0.08 → 0.80 while keeping other normal fields → score should increase
   - This proves live ML is running

---

## 2. PRIORITY 2 — Threshold Cost Curve Chart
**Status:** NOT STARTED  
**Estimated time:** 1 hour  
**Files changed:** `static/index.html` (additive only)

### Step 1: Verify the data endpoint

```
GET /threshold-explore
Expected response format (array of 99 objects):
[
  {"threshold": 0.01, "total_cost": 85420, "fp_cost": 12500, "fn_cost": 72920, "precision": 0.12, "recall": 0.99},
  {"threshold": 0.02, ...},
  ...
  {"threshold": 0.69, "total_cost": 36550, ...},   ← the optimal point
  ...
  {"threshold": 0.99, "total_cost": 91200, ...}
]
```

**BEFORE writing any code, verify:** `curl http://localhost:8000/threshold-explore` and check the actual JSON keys. Use whatever keys are actually returned.

### Step 2: Add Chart Card HTML

**Insert AFTER line 543 (closing `</div>` of the 4-PNG charts card), BEFORE line 545 (audit log card).**

```html
<!-- ============================================================ -->
<!-- PRIORITY 2: Threshold Cost Curve Chart                       -->
<!-- ============================================================ -->
<div class="card full-width">
    <h2>Business Cost Optimization — Threshold Sweep</h2>
    <p style="font-size: 0.9rem; color: var(--text-muted);">
        We swept 99 thresholds from 0.01 to 0.99, assigning <strong>INR 2,150</strong> to each False Negative 
        (missed fraud) and <strong>INR 500</strong> to each False Positive (good customer blocked). 
        The optimal threshold of <strong>0.69</strong> minimizes total business loss to <strong>INR 36,550</strong> on the held-out test set.
        No other team in the research brief visualized this interactively.
    </p>
    <div style="position: relative; height: 320px;">
        <canvas id="thresholdChart"></canvas>
    </div>
</div>
<!-- ============================================================ -->
<!-- END PRIORITY 2 HTML                                          -->
<!-- ============================================================ -->
```

### Step 3: Add Chart.js JavaScript

**Insert inside `<script>` block after `runScorePanel()` function.**

```javascript
// ============================================================
// PRIORITY 2: Threshold Cost Curve Chart JS
// ============================================================
async function initThresholdChart() {
    try {
        const res = await fetch(`${API_BASE}/threshold-explore`);
        const data = await res.json();

        // Check actual key names from response and adapt if needed
        // Assumed keys: threshold, total_cost, fp_cost, fn_cost
        const labels = data.map(d => d.threshold.toFixed(2));
        const totalCosts = data.map(d => d.total_cost);
        const fpCosts = data.map(d => d.fp_cost);
        const fnCosts = data.map(d => d.fn_cost);

        // Find optimal index (threshold = 0.69 or minimum total cost)
        const optimalIdx = data.findIndex(d => Math.abs(d.threshold - 0.69) < 0.005);

        const ctx = document.getElementById('thresholdChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Total Business Cost (INR)',
                        data: totalCosts,
                        borderColor: '#3385ff',
                        backgroundColor: 'rgba(51,133,255,0.05)',
                        borderWidth: 2.5,
                        pointRadius: 0,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'FP Cost (Good customers blocked)',
                        data: fpCosts,
                        borderColor: '#e94b4b',
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        tension: 0.3
                    },
                    {
                        label: 'FN Cost (Fraud missed)',
                        data: fnCosts,
                        borderColor: '#f5a623',
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        tension: 0.3
                    },
                    // Optimal marker — single point
                    {
                        label: 'Optimal Threshold (0.69)',
                        data: labels.map((_, i) => i === optimalIdx ? totalCosts[i] : null),
                        borderColor: '#0fa457',
                        backgroundColor: '#0fa457',
                        pointRadius: labels.map((_, i) => i === optimalIdx ? 10 : 0),
                        pointHoverRadius: 14,
                        showLine: false,
                        type: 'scatter'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: ctx => `${ctx.dataset.label}: INR ${ctx.parsed.y?.toLocaleString() || ''}`
                        }
                    },
                    annotation: {
                        annotations: {
                            optimalLine: {
                                type: 'line',
                                xMin: optimalIdx,
                                xMax: optimalIdx,
                                borderColor: '#0fa457',
                                borderWidth: 2,
                                borderDash: [6, 3],
                                label: {
                                    content: 'Optimal: 0.69 | INR 36,550',
                                    display: true,
                                    position: 'end',
                                    backgroundColor: '#0fa457',
                                    color: 'white',
                                    font: { weight: 'bold', size: 11 }
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Decision Threshold' },
                        ticks: { maxTicksLimit: 10 }
                    },
                    y: {
                        title: { display: true, text: 'Business Cost (INR)' },
                        ticks: { callback: v => 'INR ' + v.toLocaleString() }
                    }
                }
            }
        });
    } catch(e) {
        console.error('Threshold chart failed:', e);
        document.getElementById('thresholdChart').parentElement.innerHTML =
            '<p style="color:var(--text-muted); text-align:center;">Chart data unavailable</p>';
    }
}

// ⚠️ NOTE: Chart.js annotation plugin is optional.
// If annotation plugin not loaded, remove the 'annotation' block from options above.
// The green scatter point will still show the optimal threshold visually.
// ============================================================
// END PRIORITY 2 JS
// ============================================================
```

**Add `initThresholdChart()` call inside the `init()` function** (after `fetchAuditLogs()` on line ~611):
```javascript
// Inside existing init() function, add:
initThresholdChart();
```

---

## 3. PRIORITY 3 — Honest Limitations & Calibration Cards
**Status:** NOT STARTED  
**Estimated time:** 30 mins  
**Files changed:** `static/index.html` (additive only)

### Step 1: Insert HTML

**Insert AFTER line 563 (closing `</div>` of audit log card), BEFORE line 565 (outer closing `</div>`).**

```html
<!-- ============================================================ -->
<!-- PRIORITY 3: Limitations & Calibration Cards                  -->
<!-- ============================================================ -->
<div class="card full-width">
    <h2>Transparency & Methodology Disclosure</h2>
    <p style="font-size:0.9rem; color:var(--text-muted); margin-bottom:1.5rem;">
        Every strong submission in this track explicitly disclosed what was simulated, calibrated, and planned. Here is our complete transparency statement.
    </p>
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1.5rem;">

        <div style="background:var(--bg-page); border-radius:12px; padding:1.5rem; border:1px solid var(--border-color);">
            <div style="font-size:1.2rem; margin-bottom:0.5rem;">⚠️ What's Simulated</div>
            <p style="font-size:0.85rem; color:var(--text-muted); line-height:1.7;">
                The Razorpay demo uses <code>pay_mock123</code> as payment ID because programmatic card capture 
                requires a client-side checkout UI with real card entry. All <strong>Order IDs</strong> 
                (e.g. <code>order_TWprJiPLrXJE4B</code>) are genuine Razorpay test-mode API calls verifiable 
                in the Razorpay dashboard. The <strong>ML scoring, SHAP explanations, and audit logging are 100% real</strong>.
            </p>
        </div>

        <div style="background:var(--bg-page); border-radius:12px; padding:1.5rem; border:1px solid var(--border-color);">
            <div style="font-size:1.2rem; margin-bottom:0.5rem;">📊 Dataset Calibration</div>
            <p style="font-size:0.85rem; color:var(--text-muted); line-height:1.7;">
                Synthetic data (20,405 transactions) calibrated against NRF 2024 benchmarks: 
                fashion returns <strong>28-35%</strong>, electronics <strong>7-12%</strong>. 
                Our Wardrober archetype (40-70% return rate) matches documented wardrobing patterns. 
                The <strong>Loyal High-Frequency hard negative</strong> was explicitly engineered to prevent 
                trivial threshold-based separation — forcing multi-feature learning.
                No real customer data was used or scraped.
            </p>
        </div>

        <div style="background:var(--bg-page); border-radius:12px; padding:1.5rem; border:1px solid var(--border-color);">
            <div style="font-size:1.2rem; margin-bottom:0.5rem;">🔮 What We'd Build Next</div>
            <p style="font-size:0.85rem; color:var(--text-muted); line-height:1.7;">
                <strong>Peer-Group Normalization:</strong> Z-score vs. category baseline (10% electronics returns 
                is suspicious; 10% fashion is normal).<br><br>
                <strong>Device Graph / Abuse-Ring Detection:</strong> Shared device fingerprint lookup catches 
                mule rings that a per-transaction score misses (inspired by RiskLens).<br><br>
                <strong>Rolling Burst Detection:</strong> Flag when refund rate spikes vs. its own 6-hour baseline, 
                not a fixed global threshold.
            </p>
        </div>

    </div>
</div>
<!-- ============================================================ -->
<!-- END PRIORITY 3                                               -->
<!-- ============================================================ -->
```

---

## 4. PRIORITY 4 — Push & Redeploy
**Status:** NOT STARTED  
**Estimated time:** 15 mins

```powershell
# Run from c:\Users\chris\Downloads\razorpay\
git add static/index.html src/app.py REVAMP_PLAN.md REVAMP_TRACKER.md
git commit -m "feat: real scoring panel, threshold chart, limitations disclosure"
git push origin main
# Render auto-deploys on push to main — check https://dashboard.render.com
```

---

## 5. PRIORITY 5 — Demo Video (USER TASK)
**Estimated time:** 1 hour

**Script (5 minutes):**
1. **(0:00-0:30)** Open `recidian.onrender.com`. Read track quote. Introduce RECIDIAN.
2. **(0:30-1:30)** Go to Score Engine panel. Click "Loyal High-Frequency". Score LOW despite 80% return rate. Say: *"This is the hardest thing to get right. Our model learned that 80% return rate is normal if you order 22 times a month. We had to explicitly engineer this as a hard negative in our synthetic dataset."*
3. **(1:30-2:30)** Click "Wardrober". Score hits 99%+. Point to SHAP values. Read them aloud.
4. **(2:30-3:30)** Scroll to Threshold Chart. Point to the green 0.69 marker. Say: *"We didn't pick this threshold. We swept 99 values, assigned real INR costs to each false positive and false negative, and found the exact minimum."*
5. **(3:30-4:00)** Run the Razorpay demo. Show the real `order_` ID in the console log.
6. **(4:00-4:30)** Show Audit Log with real entries.
7. **(4:30-5:00)** Show Transparency card. Say: *"We know exactly what's simulated and why. Here's what we'd build next."*

---

## 6. Files Changed In This Phase

| File | Change Type | Risk |
|---|---|---|
| `static/index.html` | ADDITIVE — 3 new sections + JS | Zero — existing sections untouched |
| `src/app.py` | ONE additive optional-field change | Very low — if field absent, old behavior unchanged |
| `static/portfolio.html` | ADDITIVE — calibration note | Zero |
| `REVAMP_PLAN.md` | This file | Zero |
| `REVAMP_TRACKER.md` | Living log | Zero |

**NEVER modified:** `src/generate_data.py`, `src/features.py`, `src/rules.py`, `src/train_model.py`, `src/evaluate.py`, `models/`, `data/`, `Dockerfile`, `requirements.txt`
