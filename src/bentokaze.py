import logging
import logging.config
import os
import sqlite3

import pandas as pd
from pulp import *

from db import setup_database

# Load logging configuration
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("bentoKaze")


class BentoKazeOptimizer:
    """
    A class to optimize the selection of bento box ingredients based on nutritional
    requirements, volume constraints, and category-specific mass constraints.

    Attributes:
        db_session (sqlite3.Connection): Database session/connection.
        target_nutrition (dict): Target nutritional values for the optimization.
        max_volume (float): Maximum allowable volume for the bento box.
        min_mass_per_category (float): Minimum mass required per category.
    """

    def __init__(
        self,
        db_session,
        target_nutrition,
        max_volume,
        min_mass_per_category,
    ):
        # Use the provided database session
        logger.info("Initializing BentoKazeOptimizer")
        self.conn = db_session
        logger.info("Using provided database session")
        # Load data from the database
        self.item_data = pd.read_sql_query("SELECT * FROM items", self.conn)
        logger.info("Loaded item data from database")
        self.density_data = pd.read_sql_query("SELECT * FROM density", self.conn)
        logger.info("Loaded density data from database")
        self.nutrition_data = pd.read_sql_query("SELECT * FROM nutrition", self.conn)
        logger.info("Loaded nutrition data from database")
        self.price_data = pd.read_sql_query("SELECT * FROM price", self.conn)
        logger.info("Loaded price data from database")
        self.all_data = pd.merge(
            self.item_data,
            pd.merge(self.nutrition_data, self.price_data, on="name"),
            on="name",
        )
        logger.info("Merged all data")

        # Store the target nutrition, max volume, and min mass per category
        self.target_nutrition = target_nutrition
        self.max_volume = max_volume
        self.min_mass_per_category = min_mass_per_category
        logger.info(
            "BentoKazeOptimizer initialized with the following parameters: "
            f"target_nutrition = {target_nutrition}, "
            f"max_volume = {max_volume}, "
            f"min_mass_per_category = {min_mass_per_category}"
        )

        # Create the optimization problem
        self.prob = LpProblem("The BentoKaze Problem", LpMinimize)
        self.ingredient_vars = self._define_variables()
        logger.info("Variables defined")

        # Create a dictionary to store the density of each category
        self.density_dict = dict(
            zip(self.density_data["category"], self.density_data["density"])
        )
        logger.info("Density dictionary created")

        logger.info("BentoKazeOptimizer initialized successfully")

    def _define_variables(self):
        logger.info("Defining variables for optimization problem")
        variables = {
            row["name"]: LpVariable(row["name"], lowBound=0, cat="Continuous")
            for index, row in self.all_data.iterrows()
        }
        logger.info(f"Defined {len(variables)} variables")
        return variables

    def add_nutritional_constraints(self):
        logger.info("Adding nutritional constraints")
        constraints = {
            "fat": (">=", "TotalFat"),
            "protein": (">=", "TotalProtein"),
            "carb": ("<=", "TotalCarb"),
            "salt": ("<=", "TotalSalt"),
        }

        for nutrient, (operator, name) in constraints.items():
            logger.info(f"Adding constraint for {nutrient} with operator {operator}")
            if operator == ">=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.all_data.iterrows()
                    )
                    >= self.target_nutrition[nutrient],
                    name,
                )
                logger.info(f"Added >= constraint for {nutrient}")
            elif operator == "<=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.all_data.iterrows()
                    )
                    <= self.target_nutrition[nutrient],
                    name,
                )
                logger.info(f"Added <= constraint for {nutrient}")
        logger.info("Nutritional constraints added successfully")

    def add_volume_constraint(self):
        logger.info("Adding volume constraint")
        self.prob += (
            lpSum(
                [
                    self.ingredient_vars[row["name"]]
                    * self.density_dict[row["category"]]
                    for index, row in self.all_data.iterrows()
                ]
            )
            <= self.max_volume,
            "max_volume",
        )
        logger.info("Volume constraint added successfully")

    def add_category_constraints(self):
        logger.info("Adding category constraints")
        categories = self.all_data["category"].unique()
        for category in categories:
            logger.info(f"Adding constraint for category {category}")
            self.prob += (
                lpSum(
                    self.ingredient_vars[row["name"]]
                    for index, row in self.all_data.iterrows()
                    if row["category"] == category
                )
                >= self.min_mass_per_category,
                f"category_{category}",
            )
            logger.info(f"Added constraint for category {category}")
        logger.info("Category constraints added successfully")

    def set_objective_function(self):
        logger.info("Setting objective function to minimize total cost")
        self.prob += (
            lpSum(
                [
                    row["unit_price"] * self.ingredient_vars[row["name"]]
                    for index, row in self.all_data.iterrows()
                ]
            ),
            "TotalCost",
        )
        logger.info("Objective function set successfully")

    def solve(self, log_file="solver.log", log_path="logs"):
        logger.info("Starting to solve the optimization problem")
        if not os.path.exists(log_path):
            os.makedirs(log_path)
            logger.info(f"Created log directory at {log_path}")
        log_file = os.path.join(log_path, log_file)
        logger.info(f"Log file set to {log_file}")

        self.prob.solve(PULP_CBC_CMD(msg=True, logPath=log_file))
        logger.info("Solver finished execution")

        results = {v.name: v.varValue for v in self.prob.variables()}
        total_cost = value(self.prob.objective)

        logger.info("Optimization results obtained")
        logger.debug(f"Results: {results}")
        logger.info(f"Total cost: {total_cost}")

        return results, total_cost

    def export_problem(
        self, filename="model", export_formats=["lp"], output_dir="models"
    ):
        logger.info(
            f"Exporting problem to formats: {export_formats} in directory: {output_dir}"
        )

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory at {output_dir}")

        for fmt in export_formats:
            file_path = os.path.join(output_dir, f"{filename}.{fmt}")
            logger.info(f"Exporting problem to {file_path} in {fmt} format")
            if fmt == "mps":
                self.prob.writeMPS(file_path)
            elif fmt == "lp":
                self.prob.writeLP(file_path)
            elif fmt == "json":
                self.prob.writeJSON(file_path)
            elif fmt == "xml":
                self.prob.writeXML(file_path)
            logger.info(f"Successfully exported problem to {file_path}")
