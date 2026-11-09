
import pandas as pd
from pathlib import Path

file_path = Path(
    "scopes/scope-a-food-prices/data/raw/"
    "LKA_RTFP_mkt_2007_2026-11-02.csv"
)

df = pd.read_csv(file_path)

print("=" * 65)
print("WORLD BANK MAIN DATASET VALIDATION")
print("=" * 65)

# 1. Dataset dimensions
print("\n1. DATASET SIZE")
print("Rows:", len(df))
print("Columns:", len(df.columns))

# 2. Market coverage
print("\n2. MARKET COVERAGE")
print("Unique market names:", df["mkt_name"].nunique())
print("Unique geographic IDs:", df["geo_id"].nunique())
print("\nMarkets:")
print(sorted(df["mkt_name"].dropna().unique()))

# 3. Date coverage
df["price_date"] = pd.to_datetime(df["price_date"], errors="coerce")

print("\n3. DATE COVERAGE")
print("Start:", df["price_date"].min())
print("End:", df["price_date"].max())
print("Unique dates:", df["price_date"].nunique())

# 4. Commodity availability
commodities = [
    "rice_fao",
    "rice_various",
    "wheat_flour",
    "food_price_index"
]

print("\n4. COMMODITY AVAILABILITY")

for col in commodities:
    if col in df.columns:
        print(
            f"{col}:",
            "Available =", df[col].notna().sum(),
            "| Missing =", df[col].isna().sum()
        )

# 5. Market-date duplicates
print("\n5. DUPLICATE CHECKS")

print("Exact duplicate rows:", df.duplicated().sum())

print(
    "Duplicate market-date records:",
    df.duplicated(subset=["geo_id", "price_date"]).sum()
)

# 6. Spatial interpolation
print("\n6. SPATIAL INTERPOLATION")

print(df["spatially_interpolated"].value_counts(dropna=False))

# 7. Currency and country
print("\n7. COUNTRY AND CURRENCY")

print("Countries:", df["country"].unique())
print("Currencies:", df["currency"].unique())

# 8. Missing values
print("\n8. MISSING VALUES")

print(
    df.isna().sum()
    .sort_values(ascending=False)
    .head(20)
    .to_string()
)

# 9. Market-level sample
print("\n9. SAMPLE RECORDS")

print(
    df[
        [
            "mkt_name",
            "geo_id",
            "price_date",
            "rice_fao",
            "rice_various",
            "wheat_flour",
            "spatially_interpolated"
        ]
    ].head(10).to_string(index=False)
)

# 10. Market coverage by commodity
print("\n10. COMMODITY COVERAGE BY MARKET")

print(
    df.groupby("mkt_name")[commodities[:3]]
    .count()
    .to_string()
)

print("\nVALIDATION FINISHED")
