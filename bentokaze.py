import pandas as pd
from pulp import *


class BentoKazeOptimizer:
    def __init__(
        self,
        data_file,
        density_file,
        target_nutrition,
        max_volume,
        min_mass_per_category,
    ):
        self.data = pd.read_csv(data_file)
        self.density_data = pd.read_csv(density_file)
        self.target_nutrition = target_nutrition
        self.max_volume = max_volume
        self.min_mass_per_category = min_mass_per_category
        self.prob = LpProblem("The BentoKaze Problem", LpMinimize)
        self.ingredient_vars = self._define_variables()
        self.density_dict = dict(
            zip(self.density_data["category"], self.density_data["density"])
        )

    def _define_variables(self):
        return {
            row["name"]: LpVariable(row["name"], lowBound=0, cat="Continuous")
            for index, row in self.data.iterrows()
        }

    def add_nutritional_constraints(self):
        constraints = {
            "total_fat": (">=", "TotalFat"),
            "total_protein": (">=", "TotalProtein"),
            "total_carb": ("<=", "TotalCarb"),
            "total_salt": ("<=", "TotalSalt"),
        }

        for nutrient, (operator, name) in constraints.items():
            if operator == ">=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.data.iterrows()
                    )
                    >= self.target_nutrition[nutrient],
                    name,
                )
            elif operator == "<=":
                self.prob += (
                    lpSum(
                        row[nutrient] * self.ingredient_vars[row["name"]]
                        for index, row in self.data.iterrows()
                    )
                    <= self.target_nutrition[nutrient],
                    name,
                )

    def add_volume_constraint(self):
        self.prob += (
            lpSum(
                [
                    self.ingredient_vars[row["name"]]
                    * self.density_dict[row["category"]]
                    for index, row in self.data.iterrows()
                ]
            )
            <= self.max_volume,
            "max_volume",
        )

    def add_category_constraints(self):
        categories = self.data["category"].unique()
        for category in categories:
            self.prob += (
                lpSum(
                    self.ingredient_vars[row["name"]]
                    for index, row in self.data.iterrows()
                    if row["category"] == category
                )
                >= self.min_mass_per_category,
                f"category_{category}",
            )

    def set_objective_function(self):
        self.prob += (
            lpSum(
                [
                    row["unit_price"] * self.ingredient_vars[row["name"]]
                    for index, row in self.data.iterrows()
                ]
            ),
            "TotalCost",
        )

    def solve(self):
        self.prob.solve()
        results = {v.name: v.varValue for v in self.prob.variables()}
        total_cost = value(self.prob.objective)
        return results, total_cost

    def export_problem(self, filename):
        self.prob.writeLP(filename)


# Example usage
if __name__ == "__main__":
    target_nutrition = {
        "total_fat": 20,
        "total_protein": 50,
        "total_carb": 100,
        "total_salt": 5,
    }
    optimizer = BentoKazeOptimizer(
        "sample_data.csv", "data/food_density.csv", target_nutrition, 100, 0.5
    )
    optimizer.add_nutritional_constraints()
    optimizer.add_volume_constraint()
    optimizer.add_category_constraints()
    optimizer.set_objective_function()
    optimizer.export_problem("BentoKaze.lp")
    results, total_cost = optimizer.solve()

    for name, value in results.items():
        print(f"{name} = {value}")
    print(f"Total Cost = {total_cost}")
