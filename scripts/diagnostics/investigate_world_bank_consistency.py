
import pandas as pd

BASE = "scopes/scope-a-food-prices/data/raw/"

main_path = BASE + "LKA_RTFP_mkt_2007_2026-11-02.csv"
aggregate_path = BASE + "world_bank_food_prices_raw.csv"
model_path = BASE + "world_bank_model_info.csv"

main = pd.read_csv(main_path)
aggregate = pd.read_csv(aggregate_path)
model = pd.read_csv(model_path)

main["price_date"] = pd.to_datetime(main["price_date"])
aggregate["Date"] = pd.to_datetime(aggregate["Date"])

commodities = ["rice_fao", "rice_various", "wheat_flour"]

# 1. Compare Ampara with Market Average
print("\n1. AMPARA VS MARKET AVERAGE")

for commodity in commodities:
    comparison = main[
        main["mkt_name"].isin(["Ampara", "Market Average"])
    ][["mkt_name", "price_date", commodity]]

    pivot = comparison.pivot(
        index="price_date",
        columns="mkt_name",
        values=commodity
    )

    matched = pivot.dropna(subset=["Ampara", "Market Average"])

    print(f"\n{commodity}")
    print("Overlapping months:", len(matched))

    if len(matched) > 0:
        differences = (
            matched["Ampara"] - matched["Market Average"]
        ).abs()

        print("Exactly equal:", int((differences == 0).sum()))
        print("Different:", int((differences != 0).sum()))
        print("Maximum absolute difference:", differences.max())

        print("\nSample comparison:")
        print(matched.head(10).to_string())

# 2. Compare national series with separate aggregate CSV
print("\n2. MAIN CSV VS AGGREGATE CSV")

for commodity in commodities:
    main_series = main[
        main["mkt_name"] == "Market Average"
    ][["price_date", commodity]].rename(
        columns={commodity: "main_value"}
    )

    aggregate_series = aggregate[
        aggregate["Product"] == commodity
    ][["Date", "Close"]].rename(
        columns={"Date": "price_date", "Close": "aggregate_value"}
    )

    comparison = main_series.merge(
        aggregate_series,
        on="price_date",
        how="inner"
    ).dropna()

    print(f"\n{commodity}")
    print("Overlapping non-missing months:", len(comparison))

    if len(comparison) > 0:
        differences = (
            comparison["main_value"] -
            comparison["aggregate_value"]
        ).abs()

        print("Exactly equal:", int((differences == 0).sum()))
        print("Maximum absolute difference:", differences.max())
        print(comparison.head(5).to_string(index=False))

# 3. Compare model metadata observation counts
print("\n3. MODEL METADATA VS MAIN CSV COUNTS")

metadata_counts = {
    "rice_fao": 238,
    "rice_various": 5413,
    "wheat_flour": 1387
}

for commodity in commodities:
    actual_count = int(main[commodity].notna().sum())
    metadata_count = metadata_counts[commodity]

    print(
        f"{commodity}: "
        f"main CSV non-missing={actual_count}, "
        f"model metadata={metadata_count}"
    )

# 4. Inspect components and coverage fields
print("\n4. COMPONENTS")

print(main["components"].value_counts(dropna=False).to_string())

print("\n5. DATA COVERAGE SUMMARY")

for column in [
    "data_coverage",
    "data_coverage_recent",
    "index_confidence_score"
]:
    print(f"\n{column}")
    print(main[column].describe().to_string())

print("\nCONSISTENCY INVESTIGATION COMPLETE")
