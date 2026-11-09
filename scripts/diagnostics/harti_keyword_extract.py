
from pathlib import Path
import pdfplumber
import re
import csv

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

OUTPUT_DIR = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

keywords = [
    "rice", "nadu", "samba", "onion",
    "potato", "carrot"
]

for pdf_path in PDF_DIR.glob("*.pdf"):

    records = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_number, page in enumerate(pdf.pages, 1):

            text = page.extract_text()

            if not text:
                continue

            paragraphs = re.split(r"\n\s*\n", text)

            for paragraph in paragraphs:

                paragraph = paragraph.strip()

                if any(k in paragraph.lower() for k in keywords):

                    records.append({
                        "page": page_number,
                        "text": paragraph
                    })

    output_file = OUTPUT_DIR / (
        pdf_path.stem + "_extracts.csv"
    )

    with output_file.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["page", "text"]
        )

        writer.writeheader()
        writer.writerows(records)

    print(
        f"{pdf_path.name}: "
        f"{len(records)} relevant paragraphs extracted"
    )

print("\nExtraction completed.")
