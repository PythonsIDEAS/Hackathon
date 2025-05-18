from docx import Document
from text_anonymizer import anonymize_text  # Ensure text_anonymizer is in the same folder or a proper package

def anonymize_docx(input_docx_path, output_docx_path):
    """
    Function to anonymize the text in a DOCX file.
    """
    try:
        # Open the DOCX file
        doc = Document(input_docx_path)

        # Loop through all paragraphs in the DOCX file
        for paragraph in doc.paragraphs:
            # Anonymize the text of each paragraph
            anonymized_text = anonymize_text(paragraph.text)
            paragraph.text = anonymized_text

        # Save the anonymized DOCX file
        doc.save(output_docx_path)
        print(f"Anonymized document saved as {output_docx_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Example usage
    input_docx_path = "sample.docx"  # Ensure this is in the current directory or provide a correct path
    output_docx_path = "sample_anonymized.docx"
    anonymize_docx(input_docx_path, output_docx_path)

