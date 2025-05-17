# image_anonymizer.py

import cv2  # OpenCV for image processing
import easyocr  # EasyOCR for text detection
import numpy as np  # For array manipulation
import os  # For file operations
from text_anonymizer import anonymize_text  # Import the anonymize_text function

# Initialize EasyOCR reader for English text
reader = easyocr.Reader(['en'])

# Function to anonymize the text in an image
def anonymize_image(image_path, output_path):
    # Read the image
    image = cv2.imread(image_path)

    # Use EasyOCR to read text from the image
    results = reader.readtext(image_path)

    for (bbox, text, prob) in results:
        # Anonymize the text
        anon_text = anonymize_text(text)
        
        if anon_text != text:  # If anonymization happened
            pts = np.array(bbox).astype(int)
            # Black out the original text and put anonymized text
            cv2.rectangle(image, tuple(pts[0]), tuple(pts[2]), (0, 0, 0), -1)
            cv2.putText(image, "[АНОНИМНО]", tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Save the anonymized image
    cv2.imwrite(output_path, image)

    # Confirm the image is saved
    if os.path.exists(output_path):
        print(f"Image saved as {output_path}")
    else:
        print("Error: Image not saved properly.")

# Other functions you may have had can remain as they are
# Make sure to adjust any usage of anonymized text appropriately, as shown in the anonymize_image function

# Example usage of the function
if __name__ == "__main__":
    image_path = "input_image.jpg"  # Example image path
    output_path = "output_image.jpg"  # Example output path
    
    anonymize_image(image_path, output_path)  # Call the function to anonymize the image
