
from pathlib import Path
import pandas as pd
import re

INPUT_DIR = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)

OUTPUT_DIR = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)

# Matches ranges such as Rs.170.00-185.00/kg
# Also supports Rs.170.00 - Rs.185.00/kg
range_pattern = re.compile(
    r"Rs\.?\s*([\d,]+(?:\.\d+)?)\s*"
    r"[-–]\s*(?:Rs\.?\s*)?"
    r"([\d,]+(?:\.\d+)?)",
    re.IGNORECASE
)

# Matches individual prices such as Rs.110.00/kg
single_pattern = re.compile(
    r"Rs\.?\s*([\d,]+(?:\.\d+)?)",
    re.IGNORECASE
)

for input_file in sorted(INPUT_DIR.glob("*_extracts.csv")):

    df = pd.read_csv(input_file)
    records = []

    for _, row in df.iterrows():

        text = str(row["text"])

        ranges = list(range_pattern.finditer(text))

        for match in ranges:
            records.append({
                "source_file": input_file.name,
                "page": row["page"],
                "price_type": "range",
                "value_1": float(
                    match.group(1).replace(",", "")
                ),
                "value_2": float(
                    match.group(2).replace(",", "")
                ),
                "context": text
            })

        # Remove ranges before extracting individual prices
        remaining_text = range_pattern.sub("", text)

        for match in single_pattern.finditer(remaining_text):
            records.append({
                "source_file": input_file.name,
                "page": row["page"],
                "price_type": "single",
                "value_1": float(
                    match.group(1).replace(",", "")
                ),
                "value_2": None,
                "context": text
            })

    output_file = OUTPUT_DIR / (
        input_file.stem.replace(
            "_extracts", "_price_candidates"
        ) + ".csv"
    )

    result = pd.DataFrame(records)
    result.to_csv(output_file, index=False)

    print("\n" + input_file.name)
    print("Price candidates:", len(result))
    print(
        "Ranges:",
        (result["price_type"] == "range").sum()
    )
    print(
        "Individual prices:",
        (result["price_type"] == "single").sum()
    )

    print("\nFirst 8 candidates:")
    if not result.empty:
        for _, candidate in result.head(8).iterrows():
            print(
                f"Page {candidate['page']} | "
                f"{candidate['price_type']} | "
                f"{candidate['value_1']} - "
                f"{candidate['value_2']}"
            )
            print(
                candidate["context"][:250].replace(
                    "\n", " "
                )
            )

print("\nPrice candidate extraction completed.")
