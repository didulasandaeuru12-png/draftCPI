
from pathlib import Path
import pdfplumber
import re

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

    print("\n" + "=" * 65)
    print(pdf_path.name)
    print("=" * 65)

    page_stats = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, 1):

            if page_number < 10:
                continue

            text = page.extract_text() or ""

            numbers = re.findall(
                r"\d[\d,]*(?:\.\d+)?", text
            )

            tables = page.extract_tables()

            page_stats.append({
                "page": page_number,
                "characters": len(text),
                "numbers": len(numbers),
                "tables": len(tables),
                "preview": text[:180].replace("\n", " ")
            })

    print("Pages inspected:", len(page_stats))
    print(
        "Pages with extracted tables:",
        sum(p["tables"] > 0 for p in page_stats)
    )

    print("\n8 pages with the most numerical values:")

    for item in sorted(
        page_stats,
        key=lambda x: x["numbers"],
        reverse=True
    )[:8]:

        print(
            f"\nPage {item['page']} | "
            f"Numbers: {item['numbers']} | "
            f"Tables: {item['tables']}"
        )
        print(item["preview"])

print("\nPage structure inspection completed.")
