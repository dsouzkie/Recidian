# RECIDIAN Evaluation Report

## Core Metrics (Threshold = 0.69)
- **Precision:** 0.943 (When we flag a return, we are right 94.3% of the time)
- **Recall:** 0.930 (We catch 93.0% of all abusive returns)
- **F1 Score:** 0.937
- **ROC-AUC:** 0.994
- **PR-AUC:** 0.940

## Business Cost Impact on Test Set
- **False Positives (Good customers insulted):** 17 (Cost: INR 36,550)
- **False Negatives (Fraudsters succeeded):** 21 (Cost: INR 22,785)
- **Total Business Loss (Test Set):** INR 59,335

## Failure Case Analysis
**Type:** False Positive (Score: 0.981)
**Why did the model get it wrong?**
- order_to_return_days (0.0) increased risk by 4.902
- return_rate_90d (1.0) increased risk by 1.362
- account_age_days (42.0) increased risk by 0.869

**Root Cause:** The model heavily weighted one specific suspicious feature, overriding the overall safe profile of the user.

**What we'd do with more time:** Add peer-group normalization. The model currently looks at absolute return rates, but 10% might be high for electronics while 10% is perfectly normal for fashion. Group-relative features would fix this False Positive.
