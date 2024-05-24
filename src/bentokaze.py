import logging
import logging.config
import os
import sqlite3
from typing import Dict, List, Tuple

import pandas as pd
from pulp import *

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
        constraints (dict): Nutritional constraints for the optimization.
    """

    def __init__(
        self,
        db_session: sqlite3.Connection,
        target_nutrition: Dict[str, float],
        max_volume: float,
        min_mass_per_category: float,
        constraints: Dict[str, str],
    ):
        logger.info("Initializing BentoKazeOptimizer")
        self.conn = db_session
        self.target_nutrition = target_nutrition
        self.max_volume = max_volume
        self.min_mass_per_category = min_mass_per_category
        self.constraints = constraints

        try:
            self._load_data()
            self._initialize_problem()
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

        logger.info("BentoKazeOptimizer initialized successfully")

    def _load_data(self):
        """Load data from the database and merge into a single DataFrame."""
        try:
            self.item_data = pd.read_sql_query("SELECT * FROM items", self.conn)
            self.density_data = pd.read_sql_query("SELECT * FROM density", self.conn)
            self.nutrition_data = pd.read_sql_query(
                "SELECT * FROM nutrition", self.conn
            )
            self.price_data = pd.read_sql_query("SELECT * FROM price", self.conn)
            self.all_data = pd.merge(
                self.item_data,
                pd.merge(self.nutrition_data, self.price_data, on="name"),
                on="name",
            )
            self.density_dict = dict(
                zip(self.density_data["category"], self.density_data["density"])
            )
            logger.info("Data loaded and merged successfully")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def _initialize_problem(self):
        """Initialize the optimization problem and define variables."""
        self.prob = LpProblem("The BentoKaze Problem", LpMinimize)
        self.ingredient_vars = self._define_variables()
        logger.info("Optimization problem initialized")

    def _define_variables(self) -> Dict[str, LpVariable]:
        """Define variables for the optimization problem."""
        logger.info("Defining variables for optimization problem")
        variables = {
            row["name"]: LpVariable(row["name"], lowBound=0, cat="Continuous")
            for index, row in self.all_data.iterrows()
        }
        logger.info(f"Defined {len(variables)} variables")
        return variables

    def add_nutritional_constraints(self):
        """Add nutritional constraints to the optimization problem."""
        logger.info("Adding nutritional constraints")

        for nutrient, operator in self.constraints.items():
            logger.info(f"Adding constraint for {nutrient} with operator {operator}")
            if operator == ">=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.all_data.iterrows()
                    )
                    >= self.target_nutrition[nutrient],
                    f"Total{nutrient.capitalize()}",
                )
            elif operator == "<=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.all_data.iterrows()
                    )
                    <= self.target_nutrition[nutrient],
                    f"Total{nutrient.capitalize()}",
                )
        logger.info("Nutritional constraints added")

    def add_volume_constraint(self):
        """Add volume constraint to the optimization problem."""
        logger.info("Adding volume constraint")
        self.prob += (
            lpSum(
                self.ingredient_vars[row["name"]]
                * (1 / self.density_dict[row["category"]])
                for index, row in self.all_data.iterrows()
            )
            <= self.max_volume,
            "TotalVolume",
        )
        logger.info("Volume constraint added")

    def add_category_mass_constraints(self):
        """Add minimum mass constraints for each category."""
        logger.info("Adding category mass constraints")
        for category in self.density_dict.keys():
            self.prob += (
                lpSum(
                    self.ingredient_vars[row["name"]]
                    for index, row in self.all_data.iterrows()
                    if row["category"] == category
                )
                >= self.min_mass_per_category,
                f"MinMass_{category}",
            )
        logger.info("Category mass constraints added")

    def set_objective(self):
        """Set the objective function to minimize the total cost."""
        logger.info("Setting objective function to minimize total cost")
        self.prob += lpSum(
            row["unit_price"] * self.ingredient_vars[row["name"]]
            for index, row in self.all_data.iterrows()
        )
        logger.info("Objective function set")

    def solve(self) -> Tuple[str, Dict[str, float]]:
        """Solve the optimization problem and return the status and solution."""
        logger.info("Solving the optimization problem")
        self.prob.solve()
        status = LpStatus[self.prob.status]
        solution = {v.name: v.varValue for v in self.prob.variables() if v.varValue > 0}
        logger.info(f"Optimization problem solved with status: {status}")
        return status, solution
