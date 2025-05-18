import json
import os
import sqlite3
import mysql.connector
from faker import Faker
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

class DataAnonymizer:
    def _init_(self):
        self.faker = Faker('ru_RU')
        self.db_connection = None
        self.db_cursor = None

    def connect_to_database(self, db_type: str, **kwargs) -> bool:
        """Подключение к базе данных."""
        try:
            if db_type.lower() == 'sqlite':
                self.db_connection = sqlite3.connect(kwargs.get('database', ':memory:'))
            elif db_type.lower() == 'mysql':
                self.db_connection = mysql.connector.connect(
                    host=kwargs.get('host', 'localhost'),
                    user=kwargs.get('user'),
                    password=kwargs.get('password'),
                    database=kwargs.get('database')
                )
            else:
                raise ValueError(f'Неподдерживаемый тип базы данных: {db_type}')
            
            self.db_cursor = self.db_connection.cursor()
            return True
        except Exception as e:
            print(f'Ошибка подключения к базе данных: {str(e)}')
            return False

    def close_connection(self):
        """Закрытие подключения к базе данных."""
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def read_from_database(self, table_name: str) -> List[Dict[str, Any]]:
        """Чтение данных из таблицы."""
        try:
            self.db_cursor.execute(f'SELECT * FROM {table_name}')
            columns = [desc[0] for desc in self.db_cursor.description]
            result = []
            for row in self.db_cursor.fetchall():
                result.append(dict(zip(columns, row)))
            return result
        except Exception as e:
            print(f'Ошибка чтения из базы данных: {str(e)}')
            return []

    def write_to_database(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Запись маскированных данных в таблицу."""
        try:
            if not data:
                return False

            # Получаем структуру таблицы
            columns = list(data[0].keys())
            if isinstance(self.db_connection, sqlite3.Connection):
                placeholders = ', '.join(['?'] * len(columns))
            else:  # MySQL
                placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)

            # Очищаем существующие данные
            self.db_cursor.execute(f'DELETE FROM {table_name}')

            # Вставляем маскированные данные
            insert_query = f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})'
            values = [[row[column] for column in columns] for row in data]
            self.db_cursor.executemany(insert_query, values)
            self.db_connection.commit()
            return True
        except Exception as e:
            print(f'Ошибка записи в базу данных: {str(e)}')
            self.db_connection.rollback()
            return False

    def mask_data(self, data):
        """Маскирует данные, сохраняя часть оригинальной информации."""
        if isinstance(data, list):
            return [self.mask_data(item) for item in data]
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == 'name':
                    # Сохраняем первую букву имени и фамилии
                    parts = value.split()
                    result[key] = f"{parts[0][0]}* {parts[-1][0]}*"
                elif key == 'email':
                    # Маскируем часть email до @
                    username, domain = value.split('@')
                    masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
                    result[key] = f"{masked_username}@{domain}"
                elif key == 'phone':
                    # Оставляем только последние 4 цифры
                    digits = ''.join(filter(str.isdigit, value))
                    result[key] = f"+7 * * {digits[-4:]}"
                elif key == 'address':
                    # Маскируем номер дома и квартиры
                    parts = value.split(',')
                    masked_parts = [p.split() for p in parts]
                    for i, part in enumerate(masked_parts):
                        for j, word in enumerate(part):
                            if any(c.isdigit() for c in word):
                                part[j] = '*'
                    result[key] = ', '.join(' '.join(p) for p in masked_parts)
                elif key == 'iin':
                    # Оставляем только первые 6 цифр (дата рождения)
                    result[key] = value[:6] + '*' * 6
                else:
                    result[key] = value
            return result
        return data

    def generate_iin(self):
        """Генерирует фейковый ИИН для Казахстана."""
        birth_date = self.faker.date_of_birth()
        century_digit = '3' if birth_date.year >= 2000 else '2'
        gender_digit = str(random.choice([0, 2, 4, 6, 8]))
        date_str = birth_date.strftime('%y%m%d')
        region_code = str(random.randint(1, 99)).zfill(2)
        serial_number = str(random.randint(100, 999))
        return f"{century_digit}{date_str}{region_code}{serial_number}"

def mask_file(input_file, output_file=None):
    """Маскирует данные из JSON файла."""
    if output_file is None:
        output_file = 'masked_' + input_file

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        anonymizer = DataAnonymizer()
        masked_data = anonymizer.mask_data(data)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(masked_data, f, ensure_ascii=False, indent=2)

        print(f'Данные успешно замаскированы и сохранены в {output_file}')
        return True

    except Exception as e:
        print(f'Ошибка при маскировке данных: {str(e)}')
        return False

# Тестовые данные
sample_data = [
    {
        "name": "Воронцова Вероника Ждановна",
        "email": "ivanna_2002@example.com",
        "phone": "+7 465 518 2648",
        "address": "к. Юрьевец (Иван.), пр. Запрудный, д. 307, 774495",
        "iin": "242082777572"
    },
    {
        "name": "Клавдия Борисовна Цветкова",
        "email": "uljanrogov@example.net",
        "phone": "+7 (275) 520-76-55",
        "address": "к. Лесной (Сверд.), ш. Свободы, д. 1, 485893",
        "iin": "248021306825"
    }
]

def init_database(db_type: str, table_name: str, initial_json: str, **db_kwargs) -> bool:
    """Инициализация базы данных и загрузка начальных данных."""
    anonymizer = DataAnonymizer()
    try:
        # Проверяем наличие JSON файла или используем тестовые данные
        if not os.path.exists(initial_json):
            print(f'Файл {initial_json} не найден, используем тестовые данные')
            initial_data = [
                {
                    "name": "Иванов Иван Иванович",
                    "email": "ivanov@example.com",
                    "phone": "+7 (123) 456-7890",
                    "address": "г. Москва, ул. Примерная, д. 1, кв. 1",
                    "iin": "123456789012"
                },
                {
                    "name": "Петров Петр Петрович",
                    "email": "petrov@example.com",
                    "phone": "+7 (234) 567-8901",
                    "address": "г. Санкт-Петербург, пр. Тестовый, д. 2, кв. 2",
                    "iin": "234567890123"
                }
            ]
        else:
            # Загружаем данные из JSON
            with open(initial_json, 'r', encoding='utf-8') as f:
                initial_data = json.load(f)

        # Подключаемся к базе данных
        if not anonymizer.connect_to_database(db_type, **db_kwargs):
            return False

        # Создаем таблицу
        create_table_query = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            name TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            iin TEXT
        )
        '''
        anonymizer.db_cursor.execute(create_table_query)

        # Записываем данные в базу
        if anonymizer.write_to_database(table_name, initial_data):
            print('База данных успешно инициализирована')
            # Сохраняем копию данных в JSON
            output_json = os.path.join(os.path.dirname(_file_), 'initial_data.json')
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            print(f'Исходные данные сохранены в {output_json}')
            return True
        return False

    except Exception as e:
        print(f'Ошибка при инициализации базы данных: {str(e)}')
        return False
    finally:
        anonymizer.close_connection()

def process_database_and_json(db_type: str, table_name: str, json_file: str, **db_kwargs):
    """Обработка данных из базы данных и JSON файла."""
    anonymizer = DataAnonymizer()

    try:
        # Подключаемся к базе данных
        if not anonymizer.connect_to_database(db_type, **db_kwargs):
            return

        # Читаем данные из базы
        print('Чтение данных из базы...')
        db_data = anonymizer.read_from_database(table_name)
        if not db_data:
            print('Данные в базе не найдены')
            return

        # Маскируем данные
        print('Маскировка данных...')
        masked_data = anonymizer.mask_data(db_data)

        # Сохраняем в JSON
        print('Сохранение в JSON...')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(masked_data, f, ensure_ascii=False, indent=2)

        # Записываем обратно в базу
        print('Запись в базу данных...')
        if anonymizer.write_to_database(table_name, masked_data):
            print('Данные успешно обработаны и сохранены')
        else:
            print('Ошибка при записи в базу данных')

    except Exception as e:
        print(f'Ошибка при обработке данных: {str(e)}')
    finally:
        anonymizer.close_connection()

def main():
    # Параметры подключения к базе данных
    db_params = {
        'database': 'employees.db',  # Для SQLite
        # Для MySQL раскомментируйте и заполните следующие параметры:
        # 'host': 'localhost',
        # 'user': 'your_username',
        # 'password': 'your_password',
        # 'database': 'your_database',
    }

    # Инициализируем базу данных начальными данными
    if init_database(
        db_type='sqlite',
        table_name='employees',
        initial_json=os.path.join(os.path.dirname(_file_), 'anonymized_employees.json'),
        **db_params
    ):
        # Обрабатываем и маскируем данные
        process_database_and_json(
            db_type='sqlite',
            table_name='employees',
            json_file='masked_employees.json',
            **db_params
        )
    else:
        print('Не удалось инициализировать базу данных')

if __name__ == '__main__':
    main()