from anonymizer.text_anonymizer import anonymize_text
from anonymizer.image_anonymizer import anonymize_image

print("1 - Анонимизировать текст")
print("2 - Анонимизировать изображение")
choice = input("Выберите режим: ")

if choice == "1":
    text = input("Введите текст: ")
    print("Анонимизированный текст:\n", anonymize_text(text))

elif choice == "2":
    img_path = input("Путь к изображению: ")
    output_path = "anonymized_output.jpg"
    anonymize_image(img_path, output_path)
    print(f"Анонимизированное изображение сохранено как {output_path}")
