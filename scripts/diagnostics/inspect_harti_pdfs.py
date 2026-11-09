
from pathlib import Path
import pdfplumber
import re

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

OUTPUT_FILE = Path("harti_relevant_extracts.txt")

keywords = [
    "rice", "nadu", "samba", "onion",
    "potato", "carrot", "wholesale",
    "retail", "market", "price ranged"
]

with OUTPUT_FILE.open("w", encoding="utf-8") as output:

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

        output.write(f"\n{'=' * 70}\n")
        output.write(f"FILE: {pdf_path.name}\n")
        output.write(f"{'=' * 70}\n")

        with pdfplumber.open(pdf_path) as pdf:

            for page_number, page in enumerate(pdf.pages, 1):

                text = page.extract_text()

                if not text:
                    continue

                paragraphs = re.split(r"\n\s*\n", text)

                for paragraph in paragraphs:

                    if any(
                        keyword in paragraph.lower()
                        for keyword in keywords
                    ):
                        output.write(
                            f"\nPAGE {page_number}\n"
                        )
                        output.write(paragraph.strip())
                        output.write("\n")

print(f"Saved relevant extracts to {OUTPUT_FILE}")
