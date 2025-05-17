from flask import Flask, render_template, request, send_file
import os
import tempfile
from image_anonymizer import anonymize_image
from text_anonymizer import anonymize_text
from pdf_anoymizer import anonymize_pdf
from docx_anonymizer import anonymize_docx
from db import DatabaseAnonymizer

app = Flask(__name__)

# Temporary directory to save files
TEMP_DIR = '/tmp/anonymizer_temp/'

# Ensure the temporary directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/anonymize_text', methods=['POST'])
def anonymize_text_route():
    text = request.form['text']
    anonymized_text = anonymize_text(text)
    return render_template('result.html', result=anonymized_text, type='text')

@app.route('/anonymize_image', methods=['POST'])
def anonymize_image_route():
    if 'image' not in request.files:
        return 'No image uploaded', 400
    image = request.files['image']
    temp_path = os.path.join(TEMP_DIR, image.filename)
    image.save(temp_path)
    output_path = os.path.join(TEMP_DIR, 'anonymized_' + image.filename)
    anonymize_image(temp_path, output_path)
    return send_file(output_path, as_attachment=True)

@app.route('/anonymize_pdf', methods=['POST'])
def anonymize_pdf_route():
    if 'pdf' not in request.files:
        return 'No PDF uploaded', 400
    pdf = request.files['pdf']
    temp_path = os.path.join(TEMP_DIR, pdf.filename)
    pdf.save(temp_path)
    output_path = os.path.join(TEMP_DIR, 'anonymized_' + pdf.filename.replace('.pdf', '.txt'))
    anonymize_pdf(temp_path, output_path)
    return send_file(output_path, as_attachment=True)

@app.route('/anonymize_docx', methods=['POST'])
def anonymize_docx_route():
    if 'docx' not in request.files:
        return 'No DOCX uploaded', 400
    docx = request.files['docx']
    temp_path = os.path.join(TEMP_DIR, docx.filename)
    docx.save(temp_path)
    output_path = os.path.join(TEMP_DIR, 'anonymized_' + docx.filename)
    anonymize_docx(temp_path, output_path)
    return send_file(output_path, as_attachment=True)

@app.route('/anonymize_database', methods=['POST'])
def anonymize_database_route():
    table_name = request.form['table_name']
    columns_to_anonymize = request.form['columns_to_anonymize'].split()
    db_type = request.form['db_type']
    
    try:
        anonymizer = DatabaseAnonymizer(table_name, columns_to_anonymize)
        anonymized_data = anonymizer.anonymize_table()
        return render_template('result.html', result=anonymized_data, type='database')
    except Exception as e:
        return str(e), 400

if __name__ == '__main__':
    app.run(debug=True)