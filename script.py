import logging
import os
import sqlite3
from contextlib import closing

import yaml

from src.bentokaze import BentoKazeOptimizer
from src.db import setup_database

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_config(config_path="config.yaml"):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def setup_db_and_load_data(config):
    db_file = config["database"]["file"]
    data_path = config["data_path"]
    categories_file = os.path.join(data_path, config["data_files"]["categories"])
    items_file = os.path.join(data_path, config["data_files"]["items"])
    prices_file = os.path.join(data_path, config["data_files"]["prices"])
    setup_database(db_file, categories_file, items_file, prices_file)
    return db_file


def run_optimizer(config, db_file):
    target_nutrition = config["nutrition"]
    max_volume = config["optimizer"]["max_volume"]
    min_mass_per_category = config["optimizer"]["min_mass_per_category"]
    constraints = config["optimizer"]["constraints"]
    export_filename = config["export"]["filename"]
    export_formats = config["export"]["formats"]
    export_output_dir = config["export"]["output_dir"]

    with closing(sqlite3.connect(db_file)) as db_session:
        try:
            optimizer = BentoKazeOptimizer(
                db_session,
                target_nutrition,
                max_volume,
                min_mass_per_category,
                constraints,
            )
            optimizer.add_nutritional_constraints()
            optimizer.add_volume_constraint()
            optimizer.add_category_mass_constraints()
            optimizer.set_objective()
            status, results = optimizer.solve()

            logging.info(f"Status: {status}")
            for name, value in results.items():
                logging.info(f"{name} = {value}")

            optimizer.export_problem(
                filename=export_filename,
                export_formats=export_formats,
                output_dir=export_output_dir,
            )
        except Exception as e:
            logging.error(f"An error occurred: {e}")


def main():
    config = load_config()
    db_file = setup_db_and_load_data(config)
    run_optimizer(config, db_file)


if __name__ == "__main__":
    main()
