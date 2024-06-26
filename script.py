import logging
import logging.config
import os
import sqlite3
from contextlib import closing

import yaml

from src.bentokaze import BentoKazeOptimizer
from src.db import setup_database

# Configure logging using logging.conf
logging.config.fileConfig("logging.conf")

# Create a logger for this script
logger = logging.getLogger("script")


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


def generate_markdown_report(status, results, nutrition_values, total_volume, config):
    output_dir = config["export"]["output_dir"]
    report_filename = config["export"]["report_filename"]
    portion_size = config["food_list"].get(
        "portion_size", 100
    )  # Default to 100 if not specified
    portion_unit = config["food_list"].get(
        "portion_unit", "g"
    )  # Default to "g" if not specified

    full_path = os.path.join(output_dir, report_filename)

    report_lines = [
        "# Optimization Report",
        "",
        f"**Status:** {status}",
        "",
        "## Results",
        "",
    ]

    report_lines.append(f"| Item | Amount ({portion_unit}) |")
    report_lines.append("|------|----------------|")
    for name, value in results.items():
        stripped_name = name.strip("'\"")
        stripped_value = str(value * portion_size).strip("'\"")
        report_lines.append(f"| {stripped_name} | {stripped_value} |")

    report_lines.append("")
    report_lines.append("## Nutritional Values")
    report_lines.append("")

    report_lines.append(f"| Nutrient | Amount ({portion_unit}) |")
    report_lines.append("|----------|-----------|")
    for nutrient, value in nutrition_values.items():
        report_lines.append(f"| {nutrient.capitalize()} | {value:.2f} |")

    report_lines.append("")

    report_content = "\n".join(report_lines)

    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists
    with open(full_path, "w") as file:
        file.write(report_content)

    logger.info(f"Markdown report generated: {full_path}")


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

            if status == "Optimal":
                nutrition_values = optimizer.calculate_nutrition_values(results)
                total_volume = optimizer.calculate_total_volume(results)
                logger.info(
                    f"Nutritional values of the final output: {nutrition_values}"
                )
                logger.info(f"Total volume of the final output: {total_volume}")

            logger.info(f"Status: {status}")
            for name, value in results.items():
                logger.info(f"{name} = {value}")

            optimizer.export_problem(
                filename=export_filename,
                export_formats=export_formats,
                output_dir=export_output_dir,
            )

            return status, results, nutrition_values, total_volume

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None, None, None, None


def main():
    config = load_config()
    db_file = setup_db_and_load_data(config)
    status, results, nutrition_values, total_volume = run_optimizer(config, db_file)

    if status and results:
        generate_markdown_report(
            status, results, nutrition_values, total_volume, config
        )
        logger.info(
            f"Nutritional values and total volume calculated and report generated"
        )
    else:
        logger.error("Optimization failed or no results to report")


if __name__ == "__main__":
    main()
