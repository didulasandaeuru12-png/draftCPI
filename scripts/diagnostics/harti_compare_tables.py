
from pathlib import Path
import pdfplumber

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

target_terms = [
    "rice", "samba", "nadu", "onion",
    "potato", "carrot", "average"
]

pdf_files = sorted(PDF_DIR.glob("*.pdf"))

if not pdf_files:
    raise FileNotFoundError(f"No PDFs found in {PDF_DIR}")

for pdf_path in pdf_files:

    print("\n" + "=" * 70)
    print(pdf_path.name)
    print("=" * 70)

    with pdfplumber.open(pdf_path) as pdf:

        found = 0

        for page_number, page in enumerate(pdf.pages, 1):

            text = page.extract_text() or ""

            if "Table 14:" not in text and "Table 15:" not in text:
                continue

            found += 1
            lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            print(f"\nPDF PAGE {page_number}")

            # Show the table title and column headings
            print("\nTABLE HEADER:")
            for line in lines[:14]:
                print(line)

            # Show relevant commodity rows
            print("\nTARGET COMMODITY ROWS:")

            for line in lines[14:]:
                lower = line.lower()

                if any(term in lower for term in target_terms):
                    print(line)

        if found == 0:
            print("Tables 14 and 15 were not found.")

print("\nComparison inspection completed.")
