
from pathlib import Path
import pdfplumber

PDF_DIR = Path("scopes/scope-a-food-prices/data/raw/harti/weekly")

TARGETS = (
    "rice", "samba", "nadu", "onion",
    "potato", "carrot"
)

for pdf_path in sorted(PDF_DIR.glob("*.pdf")):

    print("\n" + "=" * 75)
    print(pdf_path.name)
    print("=" * 75)

    with pdfplumber.open(pdf_path) as pdf:

        for page_number in (25, 26):

            page = pdf.pages[page_number - 1]
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=False
            )

            midpoint = page.width / 2

            # Group words into visual rows using their vertical positions.
            words.sort(key=lambda w: (w["top"], w["x0"]))

            rows = []

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

            print(f"\nPDF PAGE {page_number}")
            print(f"Page width: {page.width:.1f}")
            print(f"Column midpoint: {midpoint:.1f}")

            for row in rows:

                left = []
                right = []

                for word in sorted(
                    row["words"], key=lambda w: w["x0"]
                ):
                    if word["x0"] < midpoint:
                        left.append(word["text"])
                    else:
                        right.append(word["text"])

                left_text = " ".join(left)
                right_text = " ".join(right)

                combined = (left_text + " " + right_text).lower()

                if any(term in combined for term in TARGETS):
                    print(f"\nY={row['top']:.1f}")
                    print(f"LEFT : {left_text}")
                    print(f"RIGHT: {right_text}")

print("\nCoordinate inspection completed.")
