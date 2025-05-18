from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import tempfile
import requests
import re
import cv2
import easyocr
import numpy as np
import pdfplumber
from docx import Document
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required
from flask_bcrypt import Bcrypt

# Initialize Flask app and configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Configure temporary directory
TEMP_DIR = '/tmp/anonymizer_temp/'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Configure reCAPTCHA
RECAPTCHA_SECRET_KEY = '6LeUKD4rAAAAAHzpW94FZS8JAZ59ls9OYa7pU7nC'

# Sensitive data patterns
patterns = {
    "IIN": r"\b\d{12}\b",
    "PHONE_NUMBER": r"\+?\d{1,3}[-\s]?\(?\d{1,4}\)?[-\s]?\d{1,4}[-\s]?\d{1,4}",
    "EMAIL_ADDRESS": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PERSON": r"\b[A-ZА-ЯЁ][a-zа-яё]+\s[A-ZА-ЯЁ][a-zа-яё]+\b"
}

# Anonymization placeholders
anonymization_placeholders = {
    "IIN": "[ИИН_АНОНИМНО]",
    "PHONE_NUMBER": "[ТЕЛ_АНОНИМНО]",
    "EMAIL_ADDRESS": "[EMAIL_АНОНИМНО]",
    "PERSON": "[ФИО_АНОНИМНО]"
}

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Anonymization functions
def anonymize_text(text):
    anonymized_text = text
    try:
        for entity, pattern in patterns.items():
            matches = re.findall(pattern, anonymized_text)
            for match in matches:
                anonymized_text = anonymized_text.replace(match, anonymization_placeholders[entity])
    except Exception as e:
        print(f"Error in text anonymization: {e}")
    return anonymized_text

def anonymize_image(image_path):
    try:
        image = cv2.imread(image_path)
        results = reader.readtext(image_path)
        
        for (bbox, text, prob) in results:
            anon_text = anonymize_text(text)
            if anon_text != text:
                pts = np.array(bbox).astype(int)
                cv2.rectangle(image, tuple(pts[0]), tuple(pts[2]), (0, 0, 0), -1)
                cv2.putText(image, "[АНОНИМНО]", tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + os.path.basename(image_path))
        cv2.imwrite(output_path, image)
        return output_path
    except Exception as e:
        print(f"Error in image anonymization: {e}")
        return None

def anonymize_pdf(pdf_path):
    try:
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + os.path.basename(pdf_path).replace('.pdf', '.txt'))
        with pdfplumber.open(pdf_path) as pdf:
            anonymized_content = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    anonymized_text = anonymize_text(text)
                    anonymized_content += f"\n--- Page {i+1} ---\n{anonymized_text}"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(anonymized_content)
        return output_path
    except Exception as e:
        print(f"Error in PDF anonymization: {e}")
        return None

def anonymize_docx(docx_path):
    try:
        doc = Document(docx_path)
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + os.path.basename(docx_path))
        
        for paragraph in doc.paragraphs:
            paragraph.text = anonymize_text(paragraph.text)
        
        doc.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error in DOCX anonymization: {e}")
        return None

# Helper functions
def verify_recaptcha(response_token):
    try:
        r = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={'secret': RECAPTCHA_SECRET_KEY, 'response': response_token}
        )
        return r.json().get('success', False)
    except:
        return False

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/text_anonymizer', methods=['GET', 'POST'])
def text_anonymizer_route():
    if request.method == 'POST':
        text = request.form.get('text', '')
        anonymized_text = anonymize_text(text)
        return render_template('text_anonymizer.html', result=anonymized_text)
    return render_template('text_anonymizer.html')

@app.route('/image_anonymizer', methods=['GET', 'POST'])
def image_anonymizer_route():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded', 'error')
            return redirect(request.url)
        
        image = request.files['image']
        if image.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        temp_path = os.path.join(TEMP_DIR, image.filename)
        image.save(temp_path)
        output_path = anonymize_image(temp_path)
        
        if output_path:
            return send_file(output_path, as_attachment=True)
        else:
            flash('Error processing image', 'error')
            return redirect(request.url)
    
    return render_template('image_anonymizer.html')

@app.route('/pdf_anonymizer', methods=['GET', 'POST'])
def pdf_anonymizer_route():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            flash('No PDF uploaded', 'error')
            return redirect(request.url)
        
        pdf = request.files['pdf']
        if pdf.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        temp_path = os.path.join(TEMP_DIR, pdf.filename)
        pdf.save(temp_path)
        output_path = anonymize_pdf(temp_path)
        
        if output_path:
            return send_file(output_path, as_attachment=True)
        else:
            flash('Error processing PDF', 'error')
            return redirect(request.url)
    
    return render_template('pdf_anonymizer.html')

@app.route('/docx_anonymizer', methods=['GET', 'POST'])
def docx_anonymizer_route():
    if request.method == 'POST':
        if 'docx' not in request.files:
            flash('No DOCX uploaded', 'error')
            return redirect(request.url)
        
        docx = request.files['docx']
        if docx.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        temp_path = os.path.join(TEMP_DIR, docx.filename)
        docx.save(temp_path)
        output_path = anonymize_docx(temp_path)
        
        if output_path:
            return send_file(output_path, as_attachment=True)
        else:
            flash('Error processing DOCX', 'error')
            return redirect(request.url)
    
    return render_template('docx_anonymizer.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'warning')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        recaptcha_response = request.form.get('g-recaptcha-response')

        if not verify_recaptcha(recaptcha_response):
            flash('Please verify that you are not a robot', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)