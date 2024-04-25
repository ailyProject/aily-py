import sqlite3
import os


class CRUDModel:
    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        if not self.db_name:
            raise RuntimeError("Please set DB_NAME in .env file")
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def _create_table(self, table_name, columns):
        columns = ', '.join(columns)
        self.cursor.execute(f"CREATE TABLE {table_name} ({columns})")
        self.conn.commit()

    def create_default_table(self):
        if os.path.exists(self.db_name):
            return

        self._create_table(
            "conversations",
            [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "created_at TEXT",
                "role TEXT",
                "msg TEXT",
            ])

    def insert(self, table_name, columns, values):
        columns = ', '.join(columns)
        values = ', '.join([f"'{value}'" for value in values])
        self.cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        self.conn.commit()

    def select(self, table_name, columns, condition=None):
        columns = ', '.join(columns)
        if condition:
            self.cursor.execute(f"SELECT {columns} FROM {table_name} WHERE {condition}")
        else:
            self.cursor.execute(f"SELECT {columns} FROM {table_name}")
        return self.cursor.fetchall()

    def update(self, table_name, columns, values, condition):
        update_values = ', '.join([f"{column} = '{value}'" for column, value in zip(columns, values)])
        self.cursor.execute(f"UPDATE {table_name} SET {update_values} WHERE {condition}")
        self.conn.commit()

    def delete(self, table_name, condition):
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
        self.conn.commit()

    def __del__(self):
        self.conn.close()
