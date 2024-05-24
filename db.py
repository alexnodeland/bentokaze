import logging
import logging.config
import sqlite3

import pandas as pd

# Load logging configuration
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("dbHelper")


class DBHelper:
    def __init__(self, db_name=":memory:"):
        self.conn = None
        self.cursor = None
        self._connect(db_name)
        self._enable_foreign_keys()
        self._create_tables()

    def _connect(self, db_name):
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            logging.info(f"Connected to database: {db_name}")
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def _enable_foreign_keys(self):
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logging.info("Foreign key support enabled.")
        except sqlite3.Error as e:
            logging.error(f"Error enabling foreign keys: {e}")
            raise

    def _create_tables(self):
        tables = {
            "density": """
                CREATE TABLE IF NOT EXISTS density (
                    category TEXT PRIMARY KEY,
                    density REAL
                )
            """,
            "food_items": """
                CREATE TABLE IF NOT EXISTS food_items (
                    name TEXT PRIMARY KEY,
                    category TEXT,
                    FOREIGN KEY (category) REFERENCES density(category)
                )
            """,
            "nutrition": """
                CREATE TABLE IF NOT EXISTS nutrition (
                    name TEXT PRIMARY KEY,
                    fat REAL,
                    carb REAL,
                    salt REAL,
                    protein REAL,
                    FOREIGN KEY (name) REFERENCES food_items(name)
                )
            """,
            "price": """
                CREATE TABLE IF NOT EXISTS price (
                    name TEXT PRIMARY KEY,
                    unit_price REAL,
                    FOREIGN KEY (name) REFERENCES food_items(name)
                )
            """,
        }

        for table, ddl in tables.items():
            try:
                self.cursor.execute(ddl)
                logging.info(f"Table '{table}' created or already exists.")
            except sqlite3.Error as e:
                logging.error(f"Error creating table '{table}': {e}")
                raise

    def load_data(self, density_file, food_items_file, nutrition_file, price_file):
        files = {
            "density": density_file,
            "food_items": food_items_file,
            "nutrition": nutrition_file,
            "price": price_file,
        }

        for table, file in files.items():
            try:
                df = pd.read_csv(file)
                df.to_sql(table, self.conn, if_exists="append", index=False)
                logging.info(f"Data loaded into table '{table}' from file '{file}'.")
            except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                logging.error(f"Error reading CSV file '{file}': {e}")
                raise
            except sqlite3.Error as e:
                logging.error(f"Error inserting data into table '{table}': {e}")
                raise

    def query_data(self, query):
        try:
            result = pd.read_sql_query(query, self.conn)
            logging.info("Query executed successfully.")
            return result
        except sqlite3.Error as e:
            logging.error(f"Error executing query: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")


def main():
    db = DBHelper()

    try:
        db.load_data(
            "data/density.csv", "data/items.csv", "data/nutrition.csv", "data/price.csv"
        )

        query = """
        SELECT fi.name, fi.category, n.fat, n.carb, n.salt, n.protein, p.unit_price, d.density
        FROM food_items fi
        JOIN nutrition n ON fi.name = n.name
        JOIN price p ON fi.name = p.name
        JOIN density d ON fi.category = d.category
        """

        result = db.query_data(query)
        print(result)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
