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
RECAPTCHA_SECRET_KEY = '6LeUKD4rAAAAAHzpW94FZS8JAZ59ls9OYa7pU7nC'

def verify_recaptcha(response_token):
    r = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': RECAPTCHA_SECRET_KEY, 'response': response_token}
    )
    result = r.json()
    return result.get('success', False)
# Ensure the temporary directory exists
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Проверка пароля
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))

        # Проверка, существует ли пользователь
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Пользователь с таким именем или email уже существует', 'warning')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация успешна. Войдите в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        recaptcha_response = request.form.get('g-recaptcha-response')

        # Проверка капчи
        if not verify_recaptcha(recaptcha_response):
            flash('Пожалуйста, подтвердите, что вы не робот', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

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