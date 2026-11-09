
from pathlib import Path
import pdfplumber

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

OUTPUT_DIR = Path(
    "scopes/scope-a-food-prices/data/extracted/harti"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

output_file = OUTPUT_DIR / "target_table_text.txt"

with output_file.open("w", encoding="utf-8") as output:

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

        output.write("\n" + "=" * 80 + "\n")
        output.write(pdf_path.name + "\n")
        output.write("=" * 80 + "\n")

        with pdfplumber.open(pdf_path) as pdf:

            for page_number in [25, 26]:

                page = pdf.pages[page_number - 1]
                text = page.extract_text() or ""

                output.write(
                    f"\n\nPDF PAGE {page_number}\n"
                )

                for line_number, line in enumerate(
                    text.splitlines(), 1
                ):
                    output.write(
                        f"{line_number:03d}: {line}\n"
                    )

print("Table text extraction completed.")
print(f"Saved to: {output_file}")

