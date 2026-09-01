import pandas as pd
from sklearn.model_selection import train_test_split
import json

def main():
    print("Loading engineered features...")
    df = pd.read_csv("data/features_engineered.csv")
    
    # Task 3.2: CRITICAL - Strip customer_archetype to prevent data leakage
    if "customer_archetype" in df.columns:
        df = df.drop(columns=["customer_archetype"])
        
    # Task 3.4: Handle NaN values
    # XGBoost handles NaNs for numeric features natively, so order_to_return_days can stay NaN.
    # However, we must encode the categorical `return_reason`.
    
    # Task 3.3: Encode categorical: return_reason
    # We will use one-hot encoding, and explicitly handle NaNs (which represent non-returned orders)
    df = pd.get_dummies(df, columns=["return_reason"], dummy_na=True, dtype=int)
    
    # Convert booleans to int (True/False -> 1/0)
    bool_cols = ["promo_code_used", "address_mismatch_flag", "same_day_reorder_after_return"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)
            
    # Define TRAINING_FEATURES list
    # Exclude IDs and the target label
    exclude_cols = ["order_id", "customer_id", "is_abusive_return"]
    TRAINING_FEATURES = [c for c in df.columns if c not in exclude_cols]
    
    print(f"Training features ({len(TRAINING_FEATURES)}):")
    for f in TRAINING_FEATURES:
        print(f" - {f}")
        
    # Task 3.6: Stratified 80/20 split
    X = df[TRAINING_FEATURES]
    y = df["is_abusive_return"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)
    
    # Print class balance
    print("\nClass Balance (Train):")
    print(y_train.value_counts(normalize=True).apply(lambda x: f"{x:.2%}"))
    
    print("\nClass Balance (Test):")
    print(y_test.value_counts(normalize=True).apply(lambda x: f"{x:.2%}"))
    
    # Task 3.7: Save train/test splits
    X_train.to_csv("data/X_train.csv", index=False)
    X_test.to_csv("data/X_test.csv", index=False)
    y_train.to_csv("data/y_train.csv", index=False)
    y_test.to_csv("data/y_test.csv", index=False)
    
    # Save the feature columns list so we can enforce exact ordering during inference
    with open("models/feature_columns.json", "w") as f:
        json.dump(TRAINING_FEATURES, f)
        
    print("\nFeature engineering and data splitting complete! Saved to data/.")

if __name__ == "__main__":
    main()
