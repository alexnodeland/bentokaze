import sqlite3

import yaml

from bentokaze import BentoKazeOptimizer
from db import setup_database

# Load configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract configuration values
db_file = config["database"]["file"]
target_nutrition = config["nutrition"]
max_volume = config["optimizer"]["max_volume"]
min_mass_per_category = config["optimizer"]["min_mass_per_category"]

# Ensure the database is set up and data is loaded
setup_database(db_file)

# Create a database session
db_session = sqlite3.connect(db_file)

try:
    # Pass the database session to the optimizer
    optimizer = BentoKazeOptimizer(
        db_session,
        target_nutrition,
        max_volume,
        min_mass_per_category,
    )
    optimizer.add_nutritional_constraints()
    optimizer.add_volume_constraint()
    optimizer.add_category_constraints()
    optimizer.set_objective_function()
    optimizer.export_problem("BentoKaze", ["lp"])
    results, total_cost = optimizer.solve()

    for name, value in results.items():
        print(f"{name} = {value}")
    print(f"Total Cost = {total_cost}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the database session
    db_session.close()
