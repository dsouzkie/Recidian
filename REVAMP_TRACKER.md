# RECIDIAN — Revamp Tracker
### Phase: POST-HACKATHON REVAMP | Created: 2026-09-02
### Last Updated: 2026-09-02 22:06 IST

---

## ⚡ AGENT RESUME PROMPT

```
I am continuing work on RECIDIAN (Razorpay AI Buildathon Track 02).
Codebase: c:\Users\chris\Downloads\razorpay\
GitHub: https://github.com/dsouzkie/Recidian
Live: https://recidian.onrender.com

READ THESE FILES FIRST (in order):
1. REVAMP_PLAN.md — full implementation plan, frozen file list, context
2. REVAMP_TRACKER.md — this file, shows exactly what's done/in-progress/blocked

CURRENT REVAMP STATUS: [CHECK § Current Session State BELOW]

DO NOT touch: src/, models/, data/, Dockerfile, requirements.txt
ALL changes are additive to: static/index.html, static/portfolio.html only
ALWAYS update this tracker after every task completed.
```

---

## § Current Session State

```
PHASE:              Revamp v2.0
CURRENT PRIORITY:   P1 — Real Scoring Panel (NOT STARTED)
LAST COMPLETED:     Planning + MD files written
BLOCKED ON:         User approval of REVAMP_PLAN.md
NEXT ACTION:        After user approves → implement Priority 1 (static/index.html only)
DEPLOYED URL:       https://recidian.onrender.com
GITHUB SHA:         755e156 (docs: finalize README, Tracker, and Implementation Plan)
KNOWN ISSUES:       Demo is scripted theater (P1 fixes this)
```

---

## § Priority Status

| Priority | Name | Status | Owner |
|---|---|---|---|
| P1 | Real Scoring Panel | `[ ] NOT STARTED` | Agent |
| P2 | Threshold Cost Curve Chart | `[ ] NOT STARTED` | Agent |
| P3 | Honest Limitations Card | `[ ] NOT STARTED` | Agent |
| P4 | GitHub Push + Redeploy | `[ ] NOT STARTED` | Agent |
| P5 | Record Demo Video | `[ ] NOT STARTED` | **USER** |

---

## § Session History

| # | Timestamp | Event | Agent | Summary |
|---|---|---|---|---|
| 1 | 2026-09-02 22:06 IST | SESSION START | Antigravity (Claude Sonnet Thinking) | Read all files. Identified scripted demo bug. Wrote REVAMP_PLAN.md and REVAMP_TRACKER.md. |

---

## § Problems & Errors Log

> Add an entry EVERY time something breaks. Never delete entries.

| # | Timestamp | Priority | Problem | Tried | Resolution | Status |
|---|---|---|---|---|---|---|
| — | — | — | No errors yet | — | — | — |

---

## § Iteration & Changes Log

> Add an entry EVERY time you deviate from REVAMP_PLAN.md.

| # | Timestamp | Priority | What Changed | Original Plan | New Approach | Why |
|---|---|---|---|---|---|---|
| — | — | — | No deviations yet | — | — | — |

---

## § Files Modified in This Phase

| # | Timestamp | Action | File | What Changed | Priority |
|---|---|---|---|---|---|
| 1 | 2026-09-02 22:06 IST | CREATED | REVAMP_PLAN.md | Full implementation plan with resume prompts | Planning |
| 2 | 2026-09-02 22:06 IST | CREATED | REVAMP_TRACKER.md | This file | Planning |

---

## § Detailed Task Log: Priority 1 — Real Scoring Panel

| # | Task | Status | Notes |
|---|---|---|---|
| P1.1 | Add scoring form HTML to index.html | `[ ]` | Sliders, number inputs, toggles, dropdown |
| P1.2 | Add scenario buttons (Normal, Wardrober, Loyal HF) | `[ ]` | Pre-fills form with profile values |
| P1.3 | Wire form to POST /score via fetch() | `[ ]` | Match ScoringFeatureInput exactly |
| P1.4 | Map return_reason dropdown to OHE fields | `[ ]` | changed_mind → return_reason_changed_mind=1 etc |
| P1.5 | Reuse existing risk gauge display | `[ ]` | Don't rebuild — call existing updateGauge() |
| P1.6 | Verify: Loyal HF scores LOW despite 80% return rate | `[ ]` | If HIGH → ML is broken, investigate |
| P1.7 | Verify: changing order_to_return_days changes score | `[ ]` | Proves live ML, not theater |

---

## § Detailed Task Log: Priority 2 — Threshold Cost Curve

| # | Task | Status | Notes |
|---|---|---|---|
| P2.1 | Fetch data from GET /threshold-explore | `[ ]` | Returns 99-point JSON array |
| P2.2 | Add Chart.js canvas to analytics section | `[ ]` | Below the 4 PNG charts |
| P2.3 | Render total_cost line (blue) | `[ ]` | X=threshold, Y=cost |
| P2.4 | Render fp_cost line (dashed red) | `[ ]` | |
| P2.5 | Render fn_cost line (dashed orange) | `[ ]` | |
| P2.6 | Add glowing marker at threshold=0.69 | `[ ]` | Label: "Optimal — INR 36,550" |

---

## § Detailed Task Log: Priority 3 — Limitations Card

| # | Task | Status | Notes |
|---|---|---|---|
| P3.1 | Add 3-column card section below dashboard | `[ ]` | "What's Simulated / Dataset Calibration / What's Next" |
| P3.2 | Card 1: What's Simulated | `[ ]` | pay_mock123 explanation |
| P3.3 | Card 2: Dataset Calibration | `[ ]` | NRF benchmarks, wardrober match |
| P3.4 | Card 3: Future Roadmap | `[ ]` | Peer-group norm, device graph, burst detection |

---

## § Verification Checklist (Run After P1-P3 Complete)

| Check | Expected | Status |
|---|---|---|
| Scoring panel visible | Yes | `[ ]` |
| "Normal Customer" button → score < 30% | Yes | `[ ]` |
| "Wardrober" button → score > 90% | Yes | `[ ]` |
| "Loyal HF" button → score < 50% despite return_rate_90d=0.80 | **CRITICAL** | `[ ]` |
| Changing sliders changes score | Yes (proves live ML) | `[ ]` |
| Threshold chart renders | Yes | `[ ]` |
| Marker visible at 0.69 | Yes | `[ ]` |
| Limitations cards visible | Yes | `[ ]` |
| Existing Razorpay demo still works | Yes (must not break) | `[ ]` |
| Audit log still populates | Yes | `[ ]` |
| recidian.onrender.com loads after push | Yes | `[ ]` |
