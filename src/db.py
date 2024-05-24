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
            logger.info(f"Connected to database: {db_name}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def _enable_foreign_keys(self):
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logger.info("Foreign key support enabled.")
        except sqlite3.Error as e:
            logger.error(f"Error enabling foreign keys: {e}")
            raise

    def _create_tables(self):
        tables = {
            "density": """
                CREATE TABLE IF NOT EXISTS density (
                    category TEXT PRIMARY KEY,
                    density REAL
                )
            """,
            "items": """
                CREATE TABLE IF NOT EXISTS items (
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
                    FOREIGN KEY (name) REFERENCES items(name)
                )
            """,
            "price": """
                CREATE TABLE IF NOT EXISTS price (
                    name TEXT PRIMARY KEY,
                    unit_price REAL,
                    FOREIGN KEY (name) REFERENCES items(name)
                )
            """,
        }

        for table, ddl in tables.items():
            try:
                self.cursor.execute(ddl)
                logger.info(f"Table '{table}' created or already exists.")
            except sqlite3.Error as e:
                logger.error(f"Error creating table '{table}': {e}")
                raise

    def load_data(self, density_file, items_file, nutrition_file, price_file):
        files = {
            "density": density_file,
            "items": items_file,
            "nutrition": nutrition_file,
            "price": price_file,
        }

        try:
            # Disable foreign key checks
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            logger.info("Foreign key checks disabled.")

            for table, file in files.items():
                df = pd.read_csv(file)
                df.to_sql(table, self.conn, if_exists="replace", index=False)
                logger.info(f"Data loaded into table '{table}' from file '{file}'.")

        except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            logger.error(f"Error reading CSV file '{file}': {e}")
            raise
        except sqlite3.Error as e:
            logger.error(f"Error inserting data into table '{table}': {e}")
            raise
        finally:
            # Re-enable foreign key checks
            self.cursor.execute("PRAGMA foreign_keys = ON")
            logger.info("Foreign key checks enabled.")

    def query_data(self, query):
        try:
            result = pd.read_sql_query(query, self.conn)
            logger.info("Query executed successfully.")
            return result
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")


def setup_database(
    db_name: str,
    density_file: str,
    items_file: str,
    nutrition_file: str,
    price_file: str,
):
    try:
        logger.info(f"Setting up database: {db_name}")
        db = DBHelper(db_name)
        db._create_tables()
        db.load_data(density_file, items_file, nutrition_file, price_file)
        logger.info("Database setup completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during database setup: {e}")
        raise
    finally:
        db.close()
        logger.info("Database connection closed.")
