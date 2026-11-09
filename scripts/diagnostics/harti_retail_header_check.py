import pdfplumber

files = [
    ("scopes/scope-a-food-prices/data/raw/harti/weekly/HARTI_weekly_2025_sample.pdf", 25),
    ("scopes/scope-a-food-prices/data/raw/harti/weekly/HARTI_weekly_latest_sample.pdf", 25),
]

for file, page_number in files:
    print("\n" + "=" * 70)
    print(file)
    print("=" * 70)

    with pdfplumber.open(file) as pdf:
        text = pdf.pages[page_number].extract_text()

        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "Table 15" in line or "Average Price Change" in line:
                print("\n".join(lines[max(0, i-2):i+7]))
