
from pathlib import Path
import pandas as pd


# ============================================================
# 1. LOAD DATASET
# ============================================================

DATA_FILE = Path(
    "scopes/scope-a-food-prices/data/extracted/"
    "harti/harti_food_prices_sample.csv"
)

df = pd.read_csv(DATA_FILE)

print("=" * 65)
print("HARTI FOOD PRICE DATA QUALITY VALIDATION")
print("=" * 65)

print(f"\nDataset shape: {df.shape}")
print(f"Total observations: {len(df)}")


# ============================================================
# 2. REQUIRED COLUMN CHECK
# ============================================================

required_columns = [
    "source_file",
    "pdf_page",
    "table_number",
    "week_number",
    "reporting_period",
    "market",
    "price_type",
    "commodity",
    "variety",
    "currency",
    "unit",
    "price_min",
    "price_max",
    "price_average",
    "previous_week_average",
    "previous_year_average",
    "change_vs_previous_week",
    "change_vs_previous_week_unit",
    "change_vs_previous_year_pct",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

print("\n--- Required columns ---")
print("Missing columns:", len(missing_columns))

if missing_columns:
    print(missing_columns)
    raise ValueError("Dataset is missing required columns.")


# ============================================================
# 3. MISSING VALUE CHECK
# ============================================================

print("\n--- Missing values ---")

missing_values = df[required_columns].isna().sum()

print(missing_values[missing_values > 0])

total_missing = int(missing_values.sum())

print("Total missing values:", total_missing)


# ============================================================
# 4. DUPLICATE CHECK
# ============================================================

duplicate_count = int(df.duplicated().sum())

duplicate_observations = int(
    df.duplicated(
        subset=[
            "source_file",
            "table_number",
            "commodity",
            "variety",
            "market",
        ]
    ).sum()
)

print("\n--- Duplicate checks ---")
print("Exact duplicate rows:", duplicate_count)
print("Duplicate commodity observations within source:", duplicate_observations)


# ============================================================
# 5. PRICE VALIDATION
# ============================================================

price_columns = [
    "price_min",
    "price_max",
    "price_average",
]

invalid_price_range = (
    df["price_min"] > df["price_max"]
)

average_outside_range = (
    (df["price_average"] < df["price_min"]) |
    (df["price_average"] > df["price_max"])
)

non_positive_prices = (
    (df[price_columns] <= 0).any(axis=1)
)

print("\n--- Price validation ---")
print(
    "Invalid price ranges:",
    int(invalid_price_range.sum())
)
print(
    "Average outside price range:",
    int(average_outside_range.sum())
)
print(
    "Non-positive prices:",
    int(non_positive_prices.sum())
)


# ============================================================
# 6. WEEKLY CHANGE VALIDATION
# ============================================================

weekly_failures = []

for index, row in df.iterrows():

    previous = row["previous_week_average"]
    current = row["price_average"]
    reported = row["change_vs_previous_week"]

    if pd.isna(previous) or pd.isna(reported):
        continue

    if previous == 0:
        continue

    if row["price_type"] == "wholesale":

        calculated = (
            (current - previous) / previous
        ) * 100

    elif row["price_type"] == "retail":

        calculated = current - previous

    else:
        weekly_failures.append(index)
        continue

    if abs(calculated - reported) > 0.15:
        weekly_failures.append(index)

print("\n--- Weekly change validation ---")
print("Invalid weekly change values:", len(weekly_failures))


# ============================================================
# 7. PREVIOUS-YEAR CHANGE VALIDATION
# ============================================================

valid_previous_year = (
    df["previous_year_average"].notna() &
    df["change_vs_previous_year_pct"].notna() &
    (df["previous_year_average"] != 0)
)

calculated_previous_year = (
    (
        df.loc[valid_previous_year, "price_average"] -
        df.loc[valid_previous_year, "previous_year_average"]
    ) /
    df.loc[valid_previous_year, "previous_year_average"]
) * 100

reported_previous_year = df.loc[
    valid_previous_year,
    "change_vs_previous_year_pct"
]

previous_year_differences = (
    calculated_previous_year - reported_previous_year
).abs()

previous_year_failures = int(
    (previous_year_differences > 0.15).sum()
)

print("\n--- Previous-year change validation ---")
print(
    "Values checked:",
    int(valid_previous_year.sum())
)
print(
    "Invalid previous-year changes:",
    previous_year_failures
)


# ============================================================
# 8. UNIT CONSISTENCY
# ============================================================

expected_units = {
    "wholesale": "%",
    "retail": "LKR/kg",
}

unit_failures = 0

for _, row in df.iterrows():

    expected = expected_units.get(row["price_type"])

    if (
        expected is None or
        row["change_vs_previous_week_unit"] != expected
    ):
        unit_failures += 1

print("\n--- Unit consistency ---")
print("Price units:", df["unit"].value_counts().to_dict())
print(
    "Weekly change units:",
    df["change_vs_previous_week_unit"].value_counts().to_dict()
)
print("Incorrect weekly change units:", unit_failures)


# ============================================================
# 9. SOURCE AND CATEGORY CONSISTENCY
# ============================================================

invalid_table_mapping = (
    (
        (df["table_number"] == 14) &
        (df["price_type"] != "wholesale")
    ) |
    (
        (df["table_number"] == 15) &
        (df["price_type"] != "retail")
    )
)

invalid_currency = df["currency"] != "LKR"

invalid_market_mapping = (
    (
        (df["table_number"] == 14) &
        (df["market"] != "Colombo")
    ) |
    (
        (df["table_number"] == 15) &
        (df["market"] != "Colombo and suburbs")
    )
)

print("\n--- Source consistency ---")
print(
    "Invalid table/price type mappings:",
    int(invalid_table_mapping.sum())
)
print(
    "Invalid currency records:",
    int(invalid_currency.sum())
)
print(
    "Invalid market mappings:",
    int(invalid_market_mapping.sum())
)


# ============================================================
# 10. FINAL VALIDATION SUMMARY
# ============================================================

checks = {
    "Missing required values": total_missing,
    "Exact duplicate rows": duplicate_count,
    "Duplicate commodity observations": duplicate_observations,
    "Invalid price ranges": int(invalid_price_range.sum()),
    "Average outside price range": int(average_outside_range.sum()),
    "Non-positive prices": int(non_positive_prices.sum()),
    "Invalid weekly changes": len(weekly_failures),
    "Invalid previous-year changes": previous_year_failures,
    "Incorrect weekly change units": unit_failures,
    "Invalid table mappings": int(invalid_table_mapping.sum()),
    "Invalid currency records": int(invalid_currency.sum()),
    "Invalid market mappings": int(invalid_market_mapping.sum()),
}

print("\n" + "=" * 65)
print("FINAL VALIDATION SUMMARY")
print("=" * 65)

for check, failures in checks.items():
    status = "PASS" if failures == 0 else "CHECK"
    print(f"{check}: {failures} [{status}]")

total_failures = sum(checks.values())

print("\nTotal validation failures:", total_failures)

if total_failures == 0:
    print("RESULT: ALL VALIDATION CHECKS PASSED")
else:
    print("RESULT: INVESTIGATION REQUIRED")

print("\n--- Dataset breakdown ---")

print("\nBy source:")
print(df["source_file"].value_counts())

print("\nBy price type:")
print(df["price_type"].value_counts())

print("\nBy commodity:")
print(df["commodity"].value_counts())

print("\nBy market:")
print(df["market"].value_counts())

print("\nValidation completed.")
print("=" * 65)
