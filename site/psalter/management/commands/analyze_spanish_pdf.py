import pdfplumber
import sys

# Try to find the PDF
pdf_path = "spanish_psalms.pdf"

print(f"Analyzing {pdf_path}...")
try:
    with pdfplumber.open(pdf_path) as pdf:
        # Check pages 1-3
        for i in [0, 1, 2]:
            if i >= len(pdf.pages):
                continue
            page = pdf.pages[i]
            print(f"\n--- Page {i+1} ---")
            print(f"Width: {page.width}, Height: {page.height}")

            # Sort chars
            chars = sorted(page.chars, key=lambda c: (c["top"], c["x0"]))

            last_top = 0
            line_text = ""
            line_meta = []

            for char in chars:
                if abs(char["top"] - last_top) > 3:
                    if line_text.strip():
                        # Analyze line
                        c = line_meta[0]
                        print(f"Text: '{line_text.strip()}'")
                        print(f"  Pos: top={c['top']:.2f}, bottom={c['bottom']:.2f}, x0={c['x0']:.2f}")
                        print(f"  Font: {c['fontname']}, Size: {c['size']:.2f}")
                    line_text = ""
                    line_meta = []
                    last_top = char["top"]

                line_text += char["text"]
                line_meta.append(char)

            if line_text.strip():
                # Analyze last line
                c = line_meta[0]
                print(f"Text: '{line_text.strip()}'")
                print(f"  Pos: top={c['top']:.2f}, bottom={c['bottom']:.2f}, x0={c['x0']:.2f}")
                print(f"  Font: {c['fontname']}, Size: {c['size']:.2f}")

except Exception as e:
    print(f"Error: {e}")
