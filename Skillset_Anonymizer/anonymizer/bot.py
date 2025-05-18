import os
import telebot
import logging
from datetime import datetime
from image_anonymizer import anonymize_image
from text_anonymizer import anonymize_text
from pdf_anoymizer import anonymize_pdf
from docx_anonymizer import anonymize_docx
from data_anonymizer import DataAnonymizer
import tempfile
import csv
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
log_dir = '/tmp/anonymizer_logs/'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f'bot_{datetime.now().strftime("%Y%m%d")}.log')

# Create a logger
logger = logging.getLogger('AnonymizerBot')
logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Create a bot instance using your bot token
API_TOKEN = '8054128372:AAGWna1SQ7jmZXARi3prt0ytqi5qsEBH2Tw'
bot = telebot.TeleBot(API_TOKEN)

# Инициализация анонимизатора и параметров базы данных
anonymizer = DataAnonymizer()
DB_PARAMS = {
    'database': 'employees.db'
}

# Temporary directory to save images (updated to use /tmp)
TEMP_DIR = '/tmp/anonymizer_temp/'

# Ensure the temporary directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Function to handle start command and show anonymization options
@bot.message_handler(commands=['start', 'help', 'mask'])
def handle_commands(message):
    if message.text == '/mask':
        try:
            # Подключаемся к базе данных
            if not anonymizer.connect_to_database('sqlite', **DB_PARAMS):
                bot.reply_to(message, 'Ошибка подключения к базе данных')
                return

            # Читаем данные из базы
            data = anonymizer.read_from_database('employees')
            if not data:
                bot.reply_to(message, 'Данные в базе не найдены')
                return

            # Маскируем данные
            masked_data = anonymizer.mask_data(data)

            # Сохраняем результат в JSON
            output_file = os.path.join(TEMP_DIR, 'masked_data.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(masked_data, f, ensure_ascii=False, indent=2)

            # Отправляем файл пользователю
            with open(output_file, 'rb') as f:
                bot.send_document(message.chat.id, f, caption='Замаскированные данные из базы')

            # Удаляем временный файл
            os.remove(output_file)

        except Exception as e:
            bot.reply_to(message, f'Произошла ошибка: {str(e)}')
        finally:
            anonymizer.close_connection()
        return
    elif message.text == '/help':
        help_text = '''
        Доступные команды:
        /start - Начать работу с ботом
        /help - Показать это сообщение
        /mask - Получить замаскированные данные из базы
        
        Поддерживаемые форматы файлов:
        - Text (txt, rtf)
        - Image (jpg, png)
        - PDF
        - DOCX
        - JSON (для маскировки данных и сохранения в базу)
        '''
        bot.reply_to(message, help_text)
        return
    logger.info(f"New session started by user {message.from_user.id}")
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Text", callback_data="text"),
               InlineKeyboardButton("Image", callback_data="image"),
               InlineKeyboardButton("PDF", callback_data="pdf"),
               InlineKeyboardButton("DOCX", callback_data="docx"),
               InlineKeyboardButton("JSON", callback_data="json"))
    bot.reply_to(message, "Welcome! Choose the type of content to anonymize:", reply_markup=markup)
    logger.info(f"Sent welcome message with options to user {message.from_user.id}")

# Function to handle button callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    logger.info(f"Callback received from user {call.from_user.id}: {call.data}")
    if call.data == "text":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the text you want to anonymize.")
        logger.info(f"Text anonymization requested by user {call.from_user.id}")
    elif call.data == "image":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the image you want to anonymize.")
        logger.info(f"Image anonymization requested by user {call.from_user.id}")
    elif call.data == "pdf":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the PDF file you want to anonymize.")
        logger.info(f"PDF anonymization requested by user {call.from_user.id}")
    elif call.data == "docx":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the DOCX file you want to anonymize.")
        logger.info(f"DOCX anonymization requested by user {call.from_user.id}")
    elif call.data == "json":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the JSON file with data to mask and save to database.")
        logger.info(f"JSON data masking requested by user {call.from_user.id}")



# Removed old process_database_info and handle_database_confirmation functions as they're no longer needed

def format_anonymized_data(data, max_rows=5):
    if not data:
        return "No data to display."
    
    headers = list(data[0].keys())
    max_lengths = {header: len(header) for header in headers}
    for row in data:
        for header in headers:
            max_lengths[header] = max(max_lengths[header], len(str(row[header])))
    
    formatted = ""
    # Add header row
    for header in headers:
        formatted += f"{header:{max_lengths[header]}} | "
    formatted = formatted.rstrip(" | ") + "\n"
    
    # Add separator line
    separator = "-" * (sum(max_lengths.values()) + (len(headers) * 3) - 1)
    formatted += separator + "\n"
    
    # Add data rows
    for row in data[:max_rows]:
        for header in headers:
            formatted += f"{str(row[header]):{max_lengths[header]}} | "
        formatted = formatted.rstrip(" | ") + "\n"
    
    if len(data) > max_rows:
        formatted += f"\n... and {len(data) - max_rows} more rows"
    
    # Use monospace formatting for Telegram
    return f"⁠ \n{formatted}\n ⁠"

def generate_anonymization_summary(table_name, columns, num_records):
    summary = f"Сводка анонимизации:\n"
    summary += f"- Таблица: {table_name}\n"
    summary += f"- Анонимизированные столбцы: {', '.join(columns)}\n"
    summary += f"- Всего обработано записей: {num_records}\n"
    return summary

@bot.callback_query_handler(func=lambda call: call.data == "show_more_data")
def handle_show_more_data(call):
    bot.answer_callback_query(call.id)
    if hasattr(bot, 'db_info') and bot.db_info:
        anonymizer = DatabaseAnonymizer(bot.db_info['table_name'], bot.db_info['columns_to_anonymize'])
        anonymized_data = anonymizer.read_anonymized_data()
        formatted_data = format_anonymized_data(anonymized_data, max_rows=10)  # Show more rows
        bot.send_message(call.message.chat.id, "Here's more anonymized data:")
        bot.send_message(call.message.chat.id, formatted_data)
    else:
        bot.send_message(call.message.chat.id, "Sorry, the anonymized data is no longer available. Please start over to anonymize new data.")

@bot.callback_query_handler(func=lambda call: call.data == "start_over")
def handle_start_over(call):
    bot.answer_callback_query(call.id)
    bot.db_info = None
    bot.anonymized_data = None
    send_welcome(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "download_data")
def handle_download_data(call):
    bot.answer_callback_query(call.id)
    if hasattr(bot, 'anonymized_data') and bot.anonymized_data:
        # Create a CSV file with anonymized data
        csv_file_path = os.path.join(TEMP_DIR, 'anonymized_data.csv')
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=bot.anonymized_data[0].keys())
            writer.writeheader()
            writer.writerows(bot.anonymized_data)
        
        # Send the CSV file to the user
        with open(csv_file_path, 'rb') as csvfile:
            bot.send_document(call.message.chat.id, csvfile, caption="Here's your anonymized data.")
        
        # Remove the temporary CSV file
        os.remove(csv_file_path)
    else:
        bot.send_message(call.message.chat.id, "Sorry, there's no anonymized data available. Please anonymize your data first.")


def format_anonymized_data(data, max_rows=5):
    if not data:
        return "No data to display."
    
    headers = list(data[0].keys())
    max_lengths = {header: len(header) for header in headers}
    for row in data:
        for header in headers:
            max_lengths[header] = max(max_lengths[header], len(str(row[header])))
    
    formatted = ""
    # Add header row
    for header in headers:
        formatted += f"{header:{max_lengths[header]}} | "
    formatted = formatted.rstrip(" | ") + "\n"
    
    # Add separator line
    separator = "-" * (sum(max_lengths.values()) + (len(headers) * 3) - 1)
    formatted += separator + "\n"
    
    # Add data rows
    for row in data[:max_rows]:
        for header in headers:
            formatted += f"{str(row[header]):{max_lengths[header]}} | "
        formatted = formatted.rstrip(" | ") + "\n"
    
    if len(data) > max_rows:
        formatted += f"\n... and {len(data) - max_rows} more rows"
    
    # Use monospace formatting for Telegram
    return f"⁠ \n{formatted}\n ⁠"

def generate_anonymization_summary(table_name, columns, num_records):
    summary = f"Сводка анонимизации:\n"
    summary += f"- Таблица: {table_name}\n"
    summary += f"- Анонимизированные столбцы: {', '.join(columns)}\n"
    summary += f"- Всего обработано записей: {num_records}\n"
    return summary


# Function to handle receiving text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    logger.info(f"Processing text anonymization request from user {message.from_user.id}")
    try:
        anonymized_text = anonymize_text(message.text)
        logger.info(f"Successfully anonymized text for user {message.from_user.id}")
        bot.reply_to(message, f"Anonymized text:\n{anonymized_text}")
    except Exception as e:
        logger.error(f"Error processing text for user {message.from_user.id}: {str(e)}")
        bot.reply_to(message, "Sorry, something went wrong while processing your text. Please try again.")

# Function to handle receiving the image
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    logger.info(f"Processing image anonymization request from user {message.from_user.id}")
    try:
        # Get the file ID of the image
        file_info = bot.get_file(message.photo[-1].file_id)
        logger.info(f"Retrieved image file info for user {message.from_user.id}")
        
        # Download the image file from Telegram servers
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save the image to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix='.jpg') as temp_file:
            temp_file.write(downloaded_file)
            temp_image_path = temp_file.name  # Get the path to the temporary file

        # Log saved image path
        print(f"Image saved as {temp_image_path}")

        # Anonymize the image (calling external anonymization function)
        output_image_path = os.path.join(TEMP_DIR, 'anonymized_image.jpg')
        anonymize_image(temp_image_path, output_image_path)

        # Send the anonymized image back to the user
        with open(output_image_path, 'rb') as output_file:
            bot.send_photo(message.chat.id, output_file)

    except Exception as e:
        logger.error(f"Error processing image for user {message.from_user.id}: {str(e)}")
        bot.reply_to(message, "Sorry, something went wrong while processing your image. Please try again.")

# Function to handle receiving PDF files
@bot.message_handler(content_types=['document'])
def handle_doc(message):
    try:
        # Define supported file types and their corresponding functions
        supported_types = {
            '.pdf': (anonymize_pdf, 'txt'),
            '.docx': (anonymize_docx, 'docx'),
            '.txt': (anonymize_text, 'txt'),
            '.doc': (anonymize_docx, 'docx'),
            '.rtf': (anonymize_text, 'txt'),
            '.json': (None, 'json'),  # For JSON files
            '.db': (None, 'db'),  # For SQLite database files
            '.sqlite': (None, 'db'),  # Alternative SQLite extension
            '.sqlite3': (None, 'db')  # Another common SQLite extension
        }

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name, file_extension = os.path.splitext(message.document.file_name)
        file_extension = file_extension.lower()

        if file_extension not in supported_types:
            supported_formats = ', '.join(supported_types.keys())
            bot.reply_to(message, f"Unsupported file type. Currently supported formats are: {supported_formats}")
            return

        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=file_extension) as temp_file:
            temp_file.write(downloaded_file)
            temp_file_path = temp_file.name

        # Handle file processing
        anonymize_func, output_ext = supported_types[file_extension]
        output_path = os.path.join(TEMP_DIR, f'{file_name}_anonymized.{output_ext}')
        
        # Special handling for JSON files
        if file_extension == '.json':
            try:
                # Читаем данные из JSON файла
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Маскируем данные
                masked_data = anonymizer.mask_data(data)

                # Подключаемся к базе данных
                if anonymizer.connect_to_database('sqlite', **DB_PARAMS):
                    try:
                        # Создаем таблицу, если её нет
                        create_table_query = '''
                        CREATE TABLE IF NOT EXISTS employees (
                            name TEXT,
                            email TEXT,
                            phone TEXT,
                            address TEXT,
                            iin TEXT
                        )
                        '''
                        anonymizer.db_cursor.execute(create_table_query)

                        # Сохраняем маскированные данные в базе
                        if anonymizer.write_to_database('employees', masked_data):
                            bot.reply_to(message, 'Данные успешно сохранены в базе данных')
                        else:
                            bot.reply_to(message, 'Ошибка при сохранении в базу данных')
                    finally:
                        anonymizer.close_connection()

                # Сохраняем результат в JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(masked_data, f, ensure_ascii=False, indent=2)

                # Отправляем результат
                with open(output_path, 'rb') as f:
                    bot.send_document(message.chat.id, f, caption='Замаскированные данные')

            except Exception as e:
                bot.reply_to(message, f'Произошла ошибка при обработке JSON файла: {str(e)}')
        else:
            # Perform regular file anonymization
            anonymize_func(temp_file_path, output_path)
            
            # Send the anonymized file back to user
            with open(output_path, 'rb') as anonymized_file:
                bot.send_document(message.chat.id, anonymized_file)

    except Exception as e:
        print(f"Error processing document: {e}")
        bot.reply_to(message, "Sorry, something went wrong while processing your document. Please try again.")
        
        # Clean up temporary files in case of error
        if 'temp_file_path' in locals():
            try:
                os.remove(temp_file_path)
            except:
                pass
        if 'output_path' in locals():
            try:
                os.remove(output_path)
            except:
                pass

# Start polling to listen for incoming messages
if __name__ == '__main__':
    logger.info("Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Critical error in bot polling: {str(e)}")
    finally:
        logger.info("Bot has stopped")