import re

# Define a dictionary with predefined sensitive data (for validation)
sensitive_data = {
    "INN": ["870512301245", "123456789012", "890123456789"],
    "names": ["Аяулым Асылбекова", "Иван Иванов", "John Doe"],
    "phone_numbers": ["+7 701 123 4567", "+1 555 555 5555"],
    "emails": ["ayaulym@example.com", "test@example.com", "john.doe@example.com"]
}

# Regular expressions to detect common sensitive data patterns
patterns = {
    "IIN": r"\b\d{12}\b",  # INN pattern (12 digits)
    "PHONE_NUMBER": r"\+?\d{1,3}[-\s]?\(?\d{1,4}\)?[-\s]?\d{1,4}[-\s]?\d{1,4}",  # Phone number pattern
    "EMAIL_ADDRESS": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email pattern
    "PERSON": r"\b[A-ZА-ЯЁ][a-zа-яё]+\s[A-ZА-ЯЁ][a-zа-яё]+\b"  # Name pattern (e.g. First Last)
}

# Anonymization placeholders
anonymization_placeholders = {
    "IIN": "[ИИН_АНОНИМНО]",
    "PHONE_NUMBER": "[ТЕЛ_АНОНИМНО]",
    "EMAIL_ADDRESS": "[EMAIL_АНОНИМНО]",
    "PERSON": "[ФИО_АНОНИМНО]"
}

# Function to anonymize text
def anonymize_text(text):
    anonymized_text = text
    
    # Try-except block to catch errors and continue processing
    try:
        # Loop through each pattern type
        for entity, pattern in patterns.items():
            matches = re.findall(pattern, anonymized_text)
            
            # For each match found, replace with the anonymization placeholder
            for match in matches:
                anonymized_text = anonymized_text.replace(match, anonymization_placeholders[entity])
    
    except Exception as e:
        print(f"An error occurred during anonymization: {e}")
    
    return anonymized_text


# Function to find and validate sensitive data using the predefined dictionary
def validate_and_find_sensitive_data(text):
    found_data = {
        "INN": [],
        "names": [],
        "phone_numbers": [],
        "emails": []
    }

    # Check for predefined sensitive data in the dictionary
    for key, data_list in sensitive_data.items():
        for data in data_list:
            if data in text:
                found_data[key].append(data)
    
    return found_data


# Main function to run the anonymization process
if __name__ == "__main__":
    # Example input text with sensitive data
    sample_text = """
    ИИН: 870512301245  
    ФИО: Аяулым Асылбекова  
    Email: ayaulym@example.com  
    Номер телефона: +7 701 123 4567  
    Адрес: Алматы, проспект Абая 55
    """

    # Validate and find any predefined sensitive data
    print("Предварительная проверка на чувствительные данные...")
    found_data = validate_and_find_sensitive_data(sample_text)
    print("Найденные данные:", found_data)
    
    # Anonymize the input text
    print("\nАнонимизированный текст:")
    anonymized_text = anonymize_text(sample_text)
    print(anonymized_text)
