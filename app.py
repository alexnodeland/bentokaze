import pandas as pd
import streamlit as st

from bentokaze import BentoKazeOptimizer

# Streamlit app
st.title("BentoKaze Optimizer")

# File upload
data_file = st.file_uploader("Upload Data CSV", type=["csv"])
density_file = st.file_uploader("Upload Density CSV", type=["csv"])

# Target nutrition inputs
st.header("Target Nutrition")
total_fat = st.number_input("Total Fat", min_value=0.0, value=20.0)
total_protein = st.number_input("Total Protein", min_value=0.0, value=50.0)
total_carb = st.number_input("Total Carbohydrates", min_value=0.0, value=100.0)
total_salt = st.number_input("Total Salt", min_value=0.0, value=5.0)

# Other constraints
max_volume = st.number_input("Max Volume", min_value=0.0, value=100.0)
min_mass_per_category = st.number_input(
    "Min Mass per Category", min_value=0.0, value=0.5
)

# Run optimization
if st.button("Optimize"):
    if data_file is not None and density_file is not None:
        # Check if files are empty
        if data_file.size == 0 or density_file.size == 0:
            st.error("One or both of the uploaded files are empty.")
        else:
            # Read the uploaded files
            data = pd.read_csv(data_file)
            density_data = pd.read_csv(density_file)

            # Create optimizer instance
            target_nutrition = {
                "total_fat": total_fat,
                "total_protein": total_protein,
                "total_carb": total_carb,
                "total_salt": total_salt,
            }
            optimizer = BentoKazeOptimizer(
                data_file,
                density_file,
                target_nutrition,
                max_volume,
                min_mass_per_category,
            )

            # Add constraints and set objective
            optimizer.add_nutritional_constraints()
            optimizer.add_volume_constraint()
            optimizer.add_category_constraints()
            optimizer.set_objective_function()

            # Solve the problem
            results, total_cost = optimizer.solve()

            # Display results
            st.header("Optimization Results")
            for name, value in results.items():
                st.write(f"{name} = {value}")
            st.write(f"Total Cost = {total_cost}")
    else:
        st.error("Please upload both data and density CSV files.")
