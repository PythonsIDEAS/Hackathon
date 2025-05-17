import sys
import os

# Add parent directory to Python path to import from anonymizer/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pdfplumber
from text_anonymizer import anonymize_text


def anonymize_pdf(input_pdf_path, output_txt_path):
    # Open and read the PDF
    with pdfplumber.open(input_pdf_path) as pdf:
        anonymized_content = ""
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            anonymized_text = anonymize_text(text)
            anonymized_content += f"\n--- Page {i+1} ---\n" + anonymized_text

    # Save anonymized output to a .txt file for now
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(anonymized_content)

    print(f"✅ Anonymized content written to: {output_txt_path}")


if __name__ == "__main__":
    # Set correct file paths
    input_pdf = "sample.pdf"
    output_txt = "sample_anonymized.txt"

    # Optional: Debug current path
    print("Current working directory:", os.getcwd())

    # Run anonymization
    anonymize_pdf(input_pdf, output_txt)
