
from pathlib import Path
import re
import csv
import pdfplumber


# ============================================================
# 1. PATH CONFIGURATION
# ============================================================

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

OUTPUT_DIR = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "harti_food_prices_sample.csv"


# ============================================================
# 2. PDF TABLE COLUMN POSITIONS
# ============================================================

# Expected horizontal positions of the seven numeric columns.
# These positions were identified through PDF coordinate inspection.

COLUMN_X = {
    (2025, 14): [
        116.9, 145.8, 169.6, 193.3, 217.1, 250.7, 275.7
    ],
    (2026, 14): [
        121.1, 149.5, 172.9, 196.3, 219.8, 253.0, 277.6
    ],
    (2025, 15): [
        117.6, 147.4, 171.3, 196.8, 221.3, 249.2, 275.1
    ],
    (2026, 15): [
        117.6, 147.4, 171.3, 196.8, 221.3, 249.2, 275.1
    ],
}


# ============================================================
# 3. OUTPUT COLUMN DEFINITIONS
# ============================================================

COLUMNS = [
    "price_min",
    "price_max",
    "price_average",
    "previous_week_average",
    "previous_year_average",
    "change_vs_previous_week",
    "change_vs_previous_year_pct",
]


# ============================================================
# 4. NUMERIC VALUE EXTRACTION
# ============================================================

def number_from_word(word):

    # Extract a numeric value from a PDF text token.
    # Handles values such as 225.00 and 225.00−.

    match = re.search(r"-?\d+(?:\.\d+)?", word)

    if not match:
        return None

    return float(match.group())


# ============================================================
# 5. COMMODITY AND VARIETY IDENTIFICATION
# ============================================================

def identify_commodity(label, section):

    label = re.sub(r"\s+", " ", label).strip().lower()

    # Identify commodity section headings.

    if label == "onion":
        return None, None, "onion"

    if label == "big onion":
        return None, None, "big_onion"

    if label == "potato":
        return None, None, "potato"

    if label == "rice":
        return None, None, "rice"

    # Rice varieties.

    if section == "rice":

        rice_varieties = {
            "samba 1": "Samba 1",
            "samba 2": "Samba 2",
            "keeri samba": "Keeri Samba",
            "nadu 1": "Nadu 1",
            "nadu 2": "Nadu 2",
        }

        if label in rice_varieties:
            return "Rice", rice_varieties[label], section

    # Onion varieties.

    if section == "onion":

        if label == "vedalan":
            return "Onion", "Vedalan", section

        if label == "imported":
            return "Onion", "Imported red onion", section

    # Big onion varieties.

    if section == "big_onion":

        if label in ("imported", "local"):
            return "Big onion", label.title(), section

    # Potato varieties.

    if section == "potato":

        potato_varieties = {
            "welimada": "Welimada",
            "n'eliya": "Nuwara Eliya",
            "imported": "Imported",
        }

        if label in potato_varieties:
            return "Potato", potato_varieties[label], section

    # Carrot.

    if label == "carrot":
        return "Vegetable", "Carrot", section

    return None, None, section


# ============================================================
# 6. PDF PAGE EXTRACTION
# ============================================================

def extract_page(page, year, table_number, pdf_path):

    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=3
    )

    words.sort(key=lambda w: (w["top"], w["x0"]))

    rows = []

    # Group words into horizontal rows using their PDF positions.

    for word in words:

        if not rows or abs(
            word["top"] - rows[-1]["top"]
        ) > 3:

            rows.append({
                "top": word["top"],
                "words": [word]
            })

        else:
            rows[-1]["words"].append(word)

    centers = COLUMN_X[(year, table_number)]

    page_text = page.extract_text() or ""

    # Extract reporting week and reporting period.

    week_match = re.search(
        r"Week\s+(\d+):\s*(.+)",
        page_text
    )

    week_number = (
        week_match.group(1)
        if week_match else None
    )

    reporting_period = (
        week_match.group(2).splitlines()[0].strip()
        if week_match else None
    )

    # Table 14 = Wholesale.
    # Table 15 = Retail.

    price_type = (
        "wholesale" if table_number == 14
        else "retail"
    )

    records = []

    section = None

    for row in rows:

        # Commodity labels are located on the left side.

        label_words = [
            w for w in row["words"]
            if w["x0"] < 100
        ]

        # Target numerical values are on the left table.

        value_words = [
            w for w in row["words"]
            if 100 <= w["x0"] < 290
        ]

        label = " ".join(
            w["text"] for w in sorted(
                label_words,
                key=lambda w: w["x0"]
            )
        )

        if not label:
            continue

        commodity, variety, section = identify_commodity(
            label,
            section
        )

        if commodity is None or not value_words:
            continue

        values = [None] * 7

        # Assign each numerical value to its nearest column.

        for word in value_words:

            number = number_from_word(word["text"])

            if number is None:
                continue

            nearest_index = min(
                range(7),
                key=lambda i: abs(
                    word["x0"] - centers[i]
                )
            )

            if abs(
                word["x0"] - centers[nearest_index]
            ) <= 10:

                values[nearest_index] = number

        # A valid average is necessary for an observation.

        if values[2] is None:
            continue

        record = {

            "source_file": pdf_path.name,

            "pdf_page": page.page_number,

            "table_number": table_number,

            "week_number": week_number,

            "reporting_period": reporting_period,

            "market": (
                "Colombo" if table_number == 14
                else "Colombo and suburbs"
            ),

            "price_type": price_type,

            "commodity": commodity,

            "variety": variety,

            "currency": "LKR",

            "unit": "kg",
        }

        record.update(dict(zip(COLUMNS, values)))

        # Weekly change has different units in the two tables:
        # Wholesale = percentage change.
        # Retail = absolute price difference in LKR/kg.

        record["change_vs_previous_week_unit"] = (
            "%" if price_type == "wholesale"
            else "LKR/kg"
        )

        records.append(record)

    return records


# ============================================================
# 7. PROCESS ALL HARTI WEEKLY PDF FILES
# ============================================================

all_records = []

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

    with pdfplumber.open(pdf_path) as pdf:

        # Read Table 14 to identify the reporting year.

        page = pdf.pages[24]

        page_text = page.extract_text() or ""

        # First try identifying the year from the filename.

        year_match = re.search(
            r"(2025|2026)",
            pdf_path.name
        )

        # If the filename has no year, use the reporting period.

        if not year_match:

            week_match = re.search(
                r"Week\s+\d+\s*:\s*.*?\b(2025|2026)\b",
                page_text,
                re.IGNORECASE
            )

            year_match = week_match

        if not year_match:

            print(
                f"SKIPPED: Could not identify year: "
                f"{pdf_path.name}"
            )

            continue

        year = int(year_match.group(1))

        print(
            f"Processing: {pdf_path.name} ({year})"
        )

        # Extract Table 14 (Wholesale) and Table 15 (Retail).

        for table_number, page_number in [
            (14, 25),
            (15, 26)
        ]:

            page = pdf.pages[page_number - 1]

            records = extract_page(
                page,
                year,
                table_number,
                pdf_path
            )

            all_records.extend(records)


# ============================================================
# 8. SAVE EXTRACTED DATASET
# ============================================================

if not all_records:

    raise RuntimeError(
        "No valid HARTI observations extracted."
    )


with OUTPUT_FILE.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=list(all_records[0].keys())
    )

    writer.writeheader()

    writer.writerows(all_records)


# ============================================================
# 9. EXTRACTION SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("HARTI FOOD PRICE EXTRACTION COMPLETED")
print("=" * 60)

print(
    f"Total extracted observations: {len(all_records)}"
)

print(f"Output: {OUTPUT_FILE}")


print("\nObservations by source file:")

for source in sorted(
    set(r["source_file"] for r in all_records)
):

    count = sum(
        r["source_file"] == source
        for r in all_records
    )

    print(f"{source}: {count}")


print("\nObservations by price type:")

for price_type in ("wholesale", "retail"):

    count = sum(
        r["price_type"] == price_type
        for r in all_records
    )

    print(f"{price_type.title()}: {count}")


print("\nObservations by commodity:")

for commodity in sorted(
    set(r["commodity"] for r in all_records)
):

    count = sum(
        r["commodity"] == commodity
        for r in all_records
    )

    print(f"{commodity}: {count}")


print("\nWeekly change units:")

for price_type in ("wholesale", "retail"):

    unit = (
        "%" if price_type == "wholesale"
        else "LKR/kg"
    )

    count = sum(
        r["price_type"] == price_type
        for r in all_records
    )

    print(
        f"{price_type.title()}: {unit} ({count} records)"
    )


print("\nSample records:")

for record in all_records[:5]:

    print(
        record["source_file"],
        record["commodity"],
        record["variety"],
        record["price_average"],
        record["price_type"],
        record["change_vs_previous_week"],
        record["change_vs_previous_week_unit"]
    )


print("\n" + "=" * 60)
print("EXTRACTION FINISHED")
print("=" * 60)
