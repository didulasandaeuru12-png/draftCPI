
import pandas as pd

BASE = "scopes/scope-a-food-prices/data/raw/"

main = pd.read_csv(
    BASE + "LKA_RTFP_mkt_2007_2026-11-02.csv"
)

aggregate = pd.read_csv(
    BASE + "world_bank_food_prices_raw.csv"
)

main["price_date"] = pd.to_datetime(main["price_date"])
aggregate["Date"] = pd.to_datetime(aggregate["Date"])

commodities = ["rice_various", "wheat_flour"]

# 1. Exact mismatches between the two files
print("\n1. EXACT PRICE MISMATCHES")

for commodity in commodities:

    main_series = main[
        main["mkt_name"] == "Market Average"
    ][["price_date", commodity]].rename(
        columns={commodity: "main_value"}
    )

    aggregate_series = aggregate[
        aggregate["Product"] == commodity
    ][["Date", "Close"]].rename(
        columns={
            "Date": "price_date",
            "Close": "aggregate_value"
        }
    )

    comparison = main_series.merge(
        aggregate_series,
        on="price_date",
        how="inner"
    ).dropna()

    mismatches = comparison[
        comparison["main_value"] != comparison["aggregate_value"]
    ].copy()

    mismatches["absolute_difference"] = (
        mismatches["main_value"] -
        mismatches["aggregate_value"]
    ).abs()

    print(f"\n{commodity}")
    print("Number of mismatches:", len(mismatches))

    print(
        mismatches.to_string(index=False)
    )

# 2. Compare Ampara and Market Average by month
print("\n2. AMPARA AND MARKET AVERAGE COMPARISON")

for commodity in commodities:

    comparison = main[
        main["mkt_name"].isin(["Ampara", "Market Average"])
    ].pivot(
        index="price_date",
        columns="mkt_name",
        values=commodity
    ).dropna()

    print(f"\n{commodity}")
    print("Total matching months:", len(comparison))

    print(
        comparison.tail(10).to_string()
    )

# 3. Check whether any other markets have identical
#    complete available series to Market Average
print("\n3. OTHER MARKETS IDENTICAL TO MARKET AVERAGE")

for commodity in commodities:

    national = main[
        main["mkt_name"] == "Market Average"
    ].set_index("price_date")[commodity].dropna()

    print(f"\n{commodity}")

    for market in sorted(main["mkt_name"].unique()):

        if market == "Market Average":
            continue

        series = main[
            main["mkt_name"] == market
        ].set_index("price_date")[commodity].dropna()

        common = pd.concat(
            [national.rename("national"), series.rename("market")],
            axis=1
        ).dropna()

        if len(common) > 0:
            identical = (
                common["national"] == common["market"]
            ).all()

            if identical:
                print(
                    market,
                    "| Identical overlapping values:",
                    len(common)
                )

print("\nPRICE MISMATCH INVESTIGATION COMPLETE")
