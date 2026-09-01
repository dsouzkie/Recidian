import pandas as pd
import numpy as np

def rule_high_return_low_orders(row):
    """return_rate_90d > 0.6 AND orders_last_90d < 4 → HIGH"""
    return row.get('return_rate_90d', 0) > 0.6 and row.get('orders_last_90d', 0) < 4

def rule_instant_promo_return(row):
    """promo_code_used AND order_to_return_days <= 1 → HIGH"""
    return row.get('promo_code_used', 0) == 1 and row.get('order_to_return_days', 999) <= 1

def rule_new_account_high_refund(row):
    """account_age_days < 30 AND return_rate_90d > 0.5 → HIGH"""
    return row.get('account_age_days', 999) < 30 and row.get('return_rate_90d', 0) > 0.5

def apply_rules(row_dict):
    """
    Applies the hardcoded rule layer to a single order/refund.
    Returns: (triggered: bool, rule_name: str, risk_band: str)
    """
    # Exclude non-returns from triggering return rules implicitly by their NaN days
    if pd.isna(row_dict.get('order_to_return_days', np.nan)):
        return False, None, "Low"
        
    if rule_high_return_low_orders(row_dict):
        return True, "high_return_low_orders", "High"
        
    if rule_instant_promo_return(row_dict):
        return True, "instant_promo_return", "High"
        
    if rule_new_account_high_refund(row_dict):
        return True, "new_account_high_refund", "High"
        
    return False, None, "Low"

def test_rules():
    print("Testing Rule Engine...")
    df = pd.read_csv("data/features_engineered.csv")
    
    # We apply rules only to refunds
    refunds_df = df[df['order_to_return_days'].notna()]
    
    results = []
    for _, row in refunds_df.iterrows():
        triggered, rule_name, band = apply_rules(row.to_dict())
        if triggered:
            results.append({
                "archetype": row.get("customer_archetype", "unknown"),
                "label": row["is_abusive_return"],
                "rule": rule_name
            })
            
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        print("\nRule Triggers by Archetype:")
        print(pd.crosstab(res_df['rule'], res_df['archetype']))
        
        print("\nRule Triggers by True Label (0=Normal, 1=Abusive):")
        print(pd.crosstab(res_df['rule'], res_df['label']))
    else:
        print("No rules triggered.")

if __name__ == "__main__":
    test_rules()
