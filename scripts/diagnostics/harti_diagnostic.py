
from pathlib import Path
import pandas as pd
import re

folder = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)

for file in sorted(folder.glob("*_extracts.csv")):
    df = pd.read_csv(file)

    print("\n" + "=" * 55)
    print(file.name)
    print("=" * 55)

    text = df["text"].fillna("").str.lower()

    checks = {
        "Total paragraphs": len(df),
        "Paragraphs containing Rs.": text.str.contains(
            r"rs\.?", regex=True
        ).sum(),
        "Paragraphs containing price ranges": text.str.contains(
            r"\d[\d,]*\.\d+\s*[-–]\s*rs?\.?\s*\d",
            regex=True
        ).sum(),
        "Paragraphs mentioning wholesale": text.str.contains(
            "wholesale"
        ).sum(),
        "Paragraphs mentioning retail": text.str.contains(
            "retail"
        ).sum(),
        "Paragraphs mentioning market": text.str.contains(
            "market"
        ).sum(),
    }

    for label, count in checks.items():
        print(f"{label}: {count}")

    print("\nCommodity mentions:")

    for commodity in [
        "rice", "nadu", "samba", "onion",
        "potato", "carrot"
    ]:
        print(
            f"{commodity}: "
            f"{text.str.contains(commodity).sum()}"
        )

    print("\nPages represented:")
    print(sorted(df["page"].dropna().unique().tolist()))

print("\nDiagnostic completed.")
