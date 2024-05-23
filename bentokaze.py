"""
Linear programming calculator to mminimize bento cost while remaining nutritious
"""

# Import necessary libraries
import pandas as pd
from pulp import *

# Read the CSV file
data = pd.read_csv("sample_data.csv")

# Create the 'prob' variable to contain the problem data
prob = LpProblem("The BentoKaze Problem", LpMinimize)

# Define the variables
ingredient_vars = {
    row["name"]: LpVariable(row["name"], lowBound=0, cat="Continuous")
    for index, row in data.iterrows()
}

# Add constraints
# Define target nutritional composition
target_nutrition = {
    "total_fat": 20,
    "total_protein": 50,
    "total_carb": 100,
    "total_salt": 5,
}

# Define constraints in a loop
constraints = {
    "total_fat": (">=", "TotalFat"),
    "total_protein": (">=", "TotalProtein"),
    "total_carb": ("<=", "TotalCarb"),
    "total_salt": ("<=", "TotalSalt"),
}

for nutrient, (operator, name) in constraints.items():
    if operator == ">=":
        prob += (
            lpSum(
                row[nutrient] * ingredient_vars[row["name"]]
                for index, row in data.iterrows()
            )
            >= target_nutrition[nutrient],
            name,
        )
    elif operator == "<=":
        prob += (
            lpSum(
                row[nutrient] * ingredient_vars[row["name"]]
                for index, row in data.iterrows()
            )
            <= target_nutrition[nutrient],
            name,
        )

# Define the volume constraint
max_volume = 100
density_data = pd.read_csv("data/food_density.csv")
density_dict = dict(zip(density_data["category"], density_data["density"]))
prob += (
    lpSum(
        [
            ingredient_vars[row["name"]] * density_dict[row["category"]]
            for index, row in data.iterrows()
        ]
    )
    <= 100,
    "max_volume",
)

# Define constraint to use at least one ingredient from each category
min_mass_per_category = 0.5
categories = data["category"].unique()
for category in categories:
    prob += (
        lpSum(
            ingredient_vars[row["name"]]
            for index, row in data.iterrows()
            if row["category"] == category
        )
        >= min_mass_per_category,
        f"category_{category}",
    )


# Define the objective function
prob += (
    lpSum(
        [
            row["unit_price"] * ingredient_vars[row["name"]]
            for index, row in data.iterrows()
        ]
    ),
    "TotalCost",
)

# Solve the problem
prob.solve()

# Print the results
for v in prob.variables():
    print(f"{v.name} = {v.varValue}")

print(f"Total Cost = {value(prob.objective)}")
