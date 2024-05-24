import os
import sqlite3

import yaml

from src.bentokaze import BentoKazeOptimizer
from src.db import setup_database

# Load configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract configuration values
db_file = config["database"]["file"]
data_path = config["data_path"]
categories_file = os.path.join(data_path, config["data_files"]["categories"])
items_file = os.path.join(data_path, config["data_files"]["items"])
prices_file = os.path.join(data_path, config["data_files"]["prices"])
target_nutrition = config["nutrition"]
max_volume = config["optimizer"]["max_volume"]
min_mass_per_category = config["optimizer"]["min_mass_per_category"]
constraints = config["optimizer"]["constraints"]
export_filename = config["export"]["filename"]
export_formats = config["export"]["formats"]
export_output_dir = config["export"]["output_dir"]

# Ensure the database is set up and data is loaded
setup_database(db_file, categories_file, items_file, prices_file)

# Create a database session
db_session = sqlite3.connect(db_file)

try:
    # Pass the database session and constraints to the optimizer
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

    print(f"Status: {status}")
    for name, value in results.items():
        print(f"{name} = {value}")

    optimizer.export_problem(
        filename=export_filename,
        export_formats=export_formats,
        output_dir=export_output_dir,
    )

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the database session
    db_session.close()
