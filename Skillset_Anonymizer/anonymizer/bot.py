import os
import telebot
from image_anonymizer import anonymize_image
from text_anonymizer import anonymize_text
from pdf_anoymizer import anonymize_pdf
from docx_anonymizer import anonymize_docx
import tempfile
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import DatabaseAnonymizer

# Create a bot instance using your bot token
API_TOKEN = '8054128372:AAGWna1SQ7jmZXARi3prt0ytqi5qsEBH2Tw'
bot = telebot.TeleBot(API_TOKEN)

# Temporary directory to save images (updated to use /tmp)
TEMP_DIR = '/tmp/anonymizer_temp/'

# Ensure the temporary directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Function to handle start command and show anonymization options
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Text", callback_data="text"),
               InlineKeyboardButton("Image", callback_data="image"),
               InlineKeyboardButton("PDF", callback_data="pdf"),
               InlineKeyboardButton("DOCX", callback_data="docx"),
               InlineKeyboardButton("Database", callback_data="database"))
    bot.reply_to(message, "Welcome! Choose the type of content to anonymize:", reply_markup=markup)

# Function to handle button callbacks
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "text":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the text you want to anonymize.")
    elif call.data == "image":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the image you want to anonymize.")
    elif call.data == "pdf":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the PDF file you want to anonymize.")
    elif call.data == "docx":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Please send the DOCX file you want to anonymize.")
    elif call.data == "database":
        bot.answer_callback_query(call.id)
        send_database_options(call.message.chat.id)

def send_database_options(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("MySQL", callback_data="db_mysql"),
        InlineKeyboardButton("PostgreSQL", callback_data="db_postgresql"),
        InlineKeyboardButton("SQLite", callback_data="db_sqlite")
    )
    bot.send_message(chat_id, "Please select the database type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("db_"))
def handle_database_type(call):
    db_type = call.data[3:]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"You selected {db_type}. Now, please provide the following information separated by commas:\ntable_name,columns_to_anonymize (space-separated)")
    bot.register_next_step_handler(call.message, process_database_info, db_type)

def process_database_info(message, db_type):
    try:
        parts = message.text.split(',')
        if len(parts) != 2:
            raise ValueError("Invalid input format. Please provide table name and columns to anonymize separated by a comma.")
        
        table_name, columns_to_anonymize = [p.strip() for p in parts]
        columns_to_anonymize = columns_to_anonymize.split()
        
        if not table_name or not columns_to_anonymize:
            raise ValueError("Table name and at least one column to anonymize must be provided.")
        
        # Confirmation step
        confirm_msg = f"Please confirm the following details:\n\nTable: {table_name}\nColumns to anonymize: {', '.join(columns_to_anonymize)}\n\nDo you want to proceed with anonymization?"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Yes", callback_data="confirm_db_yes"),
                   InlineKeyboardButton("No", callback_data="confirm_db_no"))
        bot.send_message(message.chat.id, confirm_msg, reply_markup=markup)
        
        # Store the information for later use
        bot.db_info = {
            'table_name': table_name,
            'columns_to_anonymize': columns_to_anonymize
        }
    except ValueError as ve:
        bot.reply_to(message, f"Error: {str(ve)}. Please try again.")
    except Exception as e:
        print(f"Error processing database info: {e}")
        bot.reply_to(message, f"An unexpected error occurred: {str(e)}. Please try again or contact support if the issue persists.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_db_"))
def handle_database_confirmation(call):
    bot.answer_callback_query(call.id)
    if call.data == "confirm_db_yes":
        try:
            info = bot.db_info
            anonymizer = DatabaseAnonymizer(info['table_name'], info['columns_to_anonymize'])
            anonymized_data = anonymizer.anonymize_table()
            formatted_data = format_anonymized_data(anonymized_data)
            bot.send_message(call.message.chat.id, f"Database table {info['table_name']} has been anonymized successfully. Here's a sample of the anonymized data:")
            bot.send_message(call.message.chat.id, formatted_data)
            
            # Generate a summary of the anonymization process
            summary = generate_anonymization_summary(info['table_name'], info['columns_to_anonymize'], len(anonymized_data))
            bot.send_message(call.message.chat.id, summary)
            
            # Save anonymized data for future reference
            bot.anonymized_data = anonymized_data
            
            # Offer to show more data, download anonymized data, or start over
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Show More Data", callback_data="show_more_data"),
                       InlineKeyboardButton("Download Anonymized Data", callback_data="download_data"),
                       InlineKeyboardButton("Start Over", callback_data="start_over"))
            bot.send_message(call.message.chat.id, "What would you like to do next?", reply_markup=markup)
        except Exception as e:
            print(f"Error processing database: {e}")
            bot.send_message(call.message.chat.id, f"Sorry, an error occurred while anonymizing the database: {str(e)}. Please check your input and try again.")
        finally:
            # Keep the stored database info for potential further operations
            pass
    else:
        bot.send_message(call.message.chat.id, "Database anonymization cancelled. You can start over if you wish.")
        bot.db_info = None
        bot.anonymized_data = None

def format_anonymized_data(data, max_rows=5):
    if not data:
        return "No data to display."
    
    headers = list(data[0].keys())
    formatted = " | ".join(headers) + "\n"
    formatted += "-" * len(formatted) + "\n"
    
    for row in data[:max_rows]:
        formatted += " | ".join(str(row[header]) for header in headers) + "\n"
    
    if len(data) > max_rows:
        formatted += f"\n... and {len(data) - max_rows} more rows"
    
    return f"```\n{formatted}\n```"

def generate_anonymization_summary(table_name, columns, num_records):
    summary = f"Anonymization Summary:\n"
    summary += f"- Table: {table_name}\n"
    summary += f"- Columns anonymized: {', '.join(columns)}\n"
    summary += f"- Total records processed: {num_records}\n"
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
    formatted = " | ".join(headers) + "\n"
    formatted += "-" * len(formatted) + "\n"
    
    for row in data[:max_rows]:
        formatted += " | ".join(str(row[header]) for header in headers) + "\n"
    
    if len(data) > max_rows:
        formatted += f"\n... and {len(data) - max_rows} more rows"
    
    return f"```\n{formatted}\n```"

def generate_anonymization_summary(table_name, columns, num_records):
    summary = f"Anonymization Summary:\n"
    summary += f"- Table: {table_name}\n"
    summary += f"- Columns anonymized: {', '.join(columns)}\n"
    summary += f"- Total records processed: {num_records}\n"
    return summary


# Function to handle receiving text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        anonymized_text = anonymize_text(message.text)
        bot.reply_to(message, f"Anonymized text:\n{anonymized_text}")
    except Exception as e:
        print(f"Error processing text: {e}")
        bot.reply_to(message, "Sorry, something went wrong while processing your text. Please try again.")

# Function to handle receiving the image
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        # Get the file ID of the image
        file_info = bot.get_file(message.photo[-1].file_id)
        
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
        print(f"Error processing image: {e}")
        bot.reply_to(message, "Sorry, something went wrong while processing your image. Please try again.")

# Function to handle receiving PDF files
@bot.message_handler(content_types=['document'])
def handle_doc(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name, file_extension = os.path.splitext(message.document.file_name)
        
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=file_extension) as temp_file:
            temp_file.write(downloaded_file)
            temp_file_path = temp_file.name

        if file_extension.lower() == '.pdf':
            output_path = os.path.join(TEMP_DIR, f'{file_name}_anonymized.txt')
            anonymize_pdf(temp_file_path, output_path)
            with open(output_path, 'rb') as anonymized_file:
                bot.send_document(message.chat.id, anonymized_file)
        elif file_extension.lower() == '.docx':
            output_path = os.path.join(TEMP_DIR, f'{file_name}_anonymized.docx')
            anonymize_docx(temp_file_path, output_path)
            with open(output_path, 'rb') as anonymized_file:
                bot.send_document(message.chat.id, anonymized_file)
        else:
            bot.reply_to(message, "Unsupported file type. Please send a PDF or DOCX file.")

    except Exception as e:
        print(f"Error processing document: {e}")
        bot.reply_to(message, "Sorry, something went wrong while processing your document. Please try again.")

# Start polling to listen for incoming messages
if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)
