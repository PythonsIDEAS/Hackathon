from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import tempfile
import requests
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from image_anonymizer import anonymize_image
from text_anonymizer import anonymize_text
from pdf_anoymizer import anonymize_pdf
from docx_anonymizer import anonymize_docx
from db import DatabaseAnonymizer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Temporary directory to save files
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/functionality')
def functionality():
    return render_template('functionality.html')

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

@app.route('/login', methods=['GET', 'POST'])
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
@login_required
def anonymize_text_route():
    text = request.form.get('text', '').strip()
    if not text:
        flash('Текст для анонимизации не может быть пустым', 'error')
        return redirect(url_for('index'))
    
    try:
        anonymized_text = anonymize_text(text)
        return render_template('result.html', result=anonymized_text, type='text')
    except Exception as e:
        flash(f'Ошибка при анонимизации текста: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/anonymize_image', methods=['POST'])
@login_required
def anonymize_image_route():
    if 'image' not in request.files:
        flash('Файл не был загружен', 'error')
        return redirect(url_for('index'))
    
    image = request.files['image']
    if image.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('index'))
    
    if not image.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        flash('Недопустимый формат файла. Разрешены только изображения', 'error')
        return redirect(url_for('index'))
    
    try:
        temp_path = os.path.join(TEMP_DIR, image.filename)
        image.save(temp_path)
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + image.filename)
        anonymize_image(temp_path, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Ошибка при обработке изображения: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/anonymize_pdf', methods=['POST'])
@login_required
def anonymize_pdf_route():
    if 'pdf' not in request.files:
        flash('Файл не был загружен', 'error')
        return redirect(url_for('index'))
    
    pdf = request.files['pdf']
    if pdf.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('index'))
    
    if not pdf.filename.lower().endswith('.pdf'):
        flash('Недопустимый формат файла. Разрешены только PDF файлы', 'error')
        return redirect(url_for('index'))
    
    try:
        temp_path = os.path.join(TEMP_DIR, pdf.filename)
        pdf.save(temp_path)
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + pdf.filename.replace('.pdf', '.txt'))
        anonymize_pdf(temp_path, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Ошибка при обработке PDF: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/anonymize_docx', methods=['POST'])
@login_required
def anonymize_docx_route():
    if 'docx' not in request.files:
        flash('Файл не был загружен', 'error')
        return redirect(url_for('index'))
    
    docx = request.files['docx']
    if docx.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('index'))
    
    if not docx.filename.lower().endswith('.docx'):
        flash('Недопустимый формат файла. Разрешены только DOCX файлы', 'error')
        return redirect(url_for('index'))
    
    try:
        temp_path = os.path.join(TEMP_DIR, docx.filename)
        docx.save(temp_path)
        output_path = os.path.join(TEMP_DIR, 'anonymized_' + docx.filename)
        anonymize_docx(temp_path, output_path)
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        flash(f'Ошибка при обработке DOCX: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/anonymize_database', methods=['POST'])
@login_required
def anonymize_database_route():
    table_name = request.form.get('table_name', '').strip()
    columns_to_anonymize = request.form.get('columns_to_anonymize', '').strip()
    db_type = request.form.get('db_type')
    
    if not table_name:
        flash('Название таблицы не может быть пустым', 'error')
        return redirect(url_for('index'))
    
    if not columns_to_anonymize:
        flash('Необходимо указать столбцы для анонимизации', 'error')
        return redirect(url_for('index'))
    
    if not db_type:
        flash('Необходимо выбрать тип базы данных', 'error')
        return redirect(url_for('index'))
    
    try:
        anonymizer = DatabaseAnonymizer(table_name, columns_to_anonymize.split())
        anonymized_data = anonymizer.anonymize_table()
        return render_template('result.html', result=anonymized_data, type='database')
    except Exception as e:
        flash(f'Ошибка при анонимизации базы данных: {str(e)}', 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)