
from pathlib import Path
import pdfplumber

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

OUTPUT_FILE = Path("harti_full_inspection.txt")

with OUTPUT_FILE.open("w", encoding="utf-8") as output:

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

        output.write("\n" + "=" * 80 + "\n")
        output.write(f"FILE: {pdf_path.name}\n")
        output.write("=" * 80 + "\n")

        try:
            with pdfplumber.open(pdf_path) as pdf:

                output.write(f"Total pages: {len(pdf.pages)}\n")

                for page_number, page in enumerate(
                    pdf.pages, start=1
                ):
                    output.write(
                        f"\n\n--- PAGE {page_number} ---\n"
                    )

                    try:
                        text = page.extract_text()

                        if text:
                            output.write(text)
                        else:
                            output.write(
                                "No selectable text found."
                            )

                        tables = page.extract_tables()

                        if tables:
                            output.write(
                                f"\n\nTABLES FOUND: {len(tables)}\n"
                            )

                            for table_number, table in enumerate(
                                tables, start=1
                            ):
                                output.write(
                                    f"\nTABLE {table_number}:\n"
                                )

                                for row in table:
                                    output.write(
                                        str(row) + "\n"
                                    )

                    except Exception as page_error:
                        output.write(
                            f"\nPAGE ERROR: {page_error}\n"
                        )

        except Exception as pdf_error:
            output.write(
                f"\nPDF ERROR: {pdf_error}\n"
            )

print(f"Inspection completed: {OUTPUT_FILE}")
