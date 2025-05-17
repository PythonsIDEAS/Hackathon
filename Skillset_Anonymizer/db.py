from faker import Faker
from faker.providers import BaseProvider

fake = Faker()

class KazakhstanProvider(BaseProvider):
    def iin(self):
        return self.random_number(digits=12, fix_len=True)

fake.add_provider(KazakhstanProvider)

class DatabaseAnonymizer:
    def __init__(self, table_name, columns_to_anonymize):
        self.table_name = table_name
        self.columns_to_anonymize = columns_to_anonymize
        self.data = []

    def generate_fake_data(self, num_records=100):
        for _ in range(num_records):
            record = {}
            for column in self.columns_to_anonymize:
                if column == 'name':
                    record[column] = fake.name()
                elif column == 'email':
                    record[column] = fake.email()
                elif column == 'phone':
                    record[column] = fake.phone_number()
                elif column == 'address':
                    record[column] = fake.address()
                elif column == 'date':
                    record[column] = fake.date()
                elif column == 'iin':
                    record[column] = fake.iin()
                # Add more column types as needed
            self.data.append(record)

    def anonymize_table(self):
        self.generate_fake_data()
        return self.data

    def read_anonymized_data(self):
        return self.data

# Example usage:
# anonymizer = DatabaseAnonymizer('users', ['name', 'email', 'phone', 'iin'])
# anonymized_data = anonymizer.anonymize_table()
# read_data = anonymizer.read_anonymized_data()
# anonymizer = DatabaseAnonymizer('mysql', 'localhost', 'user', 'password', 'database_name')
# anonymizer.connect()
# anonymizer.anonymize_table('users', ['name', 'email', 'phone'])
# anonymizer.close()