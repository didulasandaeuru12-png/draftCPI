
import pandas as pd

path = (
    "scopes/scope-a-food-prices/data/raw/"
    "LKA_RTFP_mkt_2007_2026-11-02.csv"
)

df = pd.read_csv(path)
df["price_date"] = pd.to_datetime(df["price_date"])

commodities = ["rice_fao", "rice_various", "wheat_flour"]

# 1. Investigate market identities
print("\n1. MARKET IDENTITIES")

markets = (
    df.groupby(["mkt_name", "geo_id"], dropna=False)
    .agg(
        latitude=("lat", "first"),
        longitude=("lon", "first"),
        records=("price_date", "count"),
        first_date=("price_date", "min"),
        last_date=("price_date", "max")
    )
    .reset_index()
)

print(markets.to_string(index=False))

# 2. Investigate possible spelling variations
print("\n2. MULAITIVU / MULLATIVU")

print(
    markets[
        markets["mkt_name"].str.contains(
            "mulai|mulla", case=False, na=False
        )
    ].to_string(index=False)
)

# 3. Inspect Market Average
print("\n3. MARKET AVERAGE")

print(
    markets[
        markets["mkt_name"].str.contains(
            "Market Average", case=False, na=False
        )
    ].to_string(index=False)
)

# 4. Commodity coverage by market
print("\n4. COMMODITY COVERAGE")

coverage = (
    df.groupby("mkt_name")[commodities]
    .agg(["count", "min", "max"])
)

print(coverage.to_string())

# 5. Market-month date continuity
print("\n5. DATE CONTINUITY")

for market in sorted(df["mkt_name"].dropna().unique()):
    subset = df[df["mkt_name"] == market]
    dates = subset["price_date"].sort_values()

    if len(dates) > 1:
        expected = pd.date_range(
            dates.min(), dates.max(), freq="MS"
        )
        missing_dates = expected.difference(dates)

        if len(missing_dates) > 0:
            print(
                market,
                "| Missing months:",
                len(missing_dates),
                "| Examples:",
                list(missing_dates[:5])
            )

# 6. Coordinate availability
print("\n6. COORDINATE AVAILABILITY")

print("Missing latitude:", df["lat"].isna().sum())
print("Missing longitude:", df["lon"].isna().sum())

print("\nMARKET INVESTIGATION COMPLETE")
