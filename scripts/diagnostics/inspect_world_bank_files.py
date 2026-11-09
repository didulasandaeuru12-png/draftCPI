
import pandas as pd
import os

base = "scopes/scope-a-food-prices/data/raw"

files = [
    "world_bank_ticker_info.csv",
    "world_bank_model_info.csv"
]

for filename in files:
    path = os.path.join(base, filename)

    print("\n" + "=" * 70)
    print("FILE:", filename)
    print("=" * 70)

    if not os.path.exists(path):
        print("FILE NOT FOUND:", path)
        continue

    df = pd.read_csv(path)

    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 10 rows:")
    print(df.head(10).to_string(index=False))

    print("\nMissing values:")
    print(df.isna().sum().to_string())
