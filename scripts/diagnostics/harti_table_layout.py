from pathlib import Path
import pdfplumber

PDF_DIR = Path(
    "scopes/scope-a-food-prices/data/raw/harti/weekly"
)

PDF_NAME = "HARTI_weekly_latest_sample.pdf"

TARGET_PAGES = [12, 13, 16, 17, 25, 26]

pdf_path = PDF_DIR / PDF_NAME

with pdfplumber.open(pdf_path) as pdf:

    for page_number in TARGET_PAGES:

        page = pdf.pages[page_number - 1]

        print(f"\n{'=' * 65}")
        print(f"PAGE {page_number}")
        print("=" * 65)

        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=3,
            keep_blank_chars=False
        )

        # Group words into lines using their vertical positions
        lines = {}

        for word in words:
            y = round(word["top"] / 3) * 3
            lines.setdefault(y, []).append(word)

        for y in sorted(lines):

            line_words = sorted(
                lines[y],
                key=lambda word: word["x0"]
            )

            text = " ".join(
                word["text"] for word in line_words
            )

            if any(
                keyword in text.lower()
                for keyword in [
                    "colombo", "gampaha", "carrot",
                    "potato", "onion", "rice",
                    "locations", "nadu", "samba"
                ]
            ) or any(
                any(char.isdigit() for char in word["text"])
                for word in line_words
            ):

                print(text[:220])

print("\nPDF position inspection completed.")