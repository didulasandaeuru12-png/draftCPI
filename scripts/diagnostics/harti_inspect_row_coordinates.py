
from pathlib import Path
import pdfplumber

PDF_DIR = Path("scopes/scope-a-food-prices/data/raw/harti/weekly")

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

    print("\n" + "=" * 75)
    print(pdf_path.name)
    print("=" * 75)

    with pdfplumber.open(pdf_path) as pdf:

        for page_number in (25, 26):

            page = pdf.pages[page_number - 1]

            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3
            )

            selected = [
                word for word in words
                if 260 <= word["top"] <= 510
            ]

            selected.sort(
                key=lambda word: (round(word["top"], 1), word["x0"])
            )

            rows = []

            for word in selected:

                y = round(word["top"], 1)

                if not rows or abs(y - rows[-1]["y"]) > 3:
                    rows.append({"y": y, "words": []})

                rows[-1]["words"].append(word)

            print(f"\nPAGE {page_number}")

            for row in rows:

                details = [
                    f'{w["x0"]:.1f}:{w["text"]}'
                    for w in row["words"]
                ]

                print(f'Y={row["y"]:.1f} | ' + " | ".join(details))

print("\nDetailed coordinate inspection completed.")
