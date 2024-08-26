import json
import os
from typing import Dict, List

import pandas as pd


def _transform_str_for_bids_filename(filename: str):
    """Replace spaces in a string with hyphens to match BIDS string format rules.."""
    return filename.replace(" ", "-")


def reformat_resources(input_dir: str, output_dir: str) -> None:
    """
    Converts lists from all JSON files in the input directory to dictionaries
    where each list item becomes a key in the dictionary with a value of
    {"description": ""}, and saves them to the output directory with the same filename.

    Args:
        input_dir (str): The directory path containing input JSON files with lists.
        output_dir (str): The directory path to save the output JSON dictionary files.

    Raises:
        ValueError: If input_dir and output_dir are the same.
        FileNotFoundError: If input_dir does not exist.
        Exception: If any unexpected error occurs during file processing.

    Returns:
        None
    """
    # Check if input and output directories are the same
    if os.path.abspath(input_dir) == os.path.abspath(output_dir):
        raise ValueError("Input and output directories must be different.")

    # Check if input directory exists
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")

    # Create output directory if it does not exist
    os.makedirs(output_dir, exist_ok=True)

    # Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            input_json_path = os.path.join(input_dir, filename)
            output_json_path = os.path.join(output_dir, filename)
            print(output_json_path)

            try:
                # Load the list from the input JSON file
                with open(input_json_path, "r") as input_file:
                    keys_list: List[str] = json.load(input_file)
                result_dict: Dict[str, Dict[str, str]] = {
                    key: {"description": ""} for key in keys_list
                }

                # Save the resulting dictionary to the output JSON file
                with open(output_json_path, "w") as output_file:
                    json.dump(result_dict, output_file, indent=4)

            except Exception as e:
                print(f"Error processing file '{filename}': {e}")


def make_tsv_files(directory: str) -> None:
    """
    Creates .tsv files for each .json file present in the specified directory.
    The .tsv files will have columns corresponding to the keys of the JSON files,
    maintaining the order of the keys.

    Args:
        directory (str): The path to the directory containing .json files for which
                         .tsv files need to be created.

    Returns:
        None

    Raises:
        FileNotFoundError: If the specified directory does not exist.
        Exception: If any unexpected error occurs during file creation.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory '{directory}' does not exist.")

    # Iterate over all files in the specified directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            base_name = os.path.splitext(filename)[0]
            tsv_filename = f"{base_name}.tsv"
            json_filepath = os.path.join(directory, filename)
            tsv_filepath = os.path.join(directory, tsv_filename)

            try:
                with open(json_filepath, "r") as json_file:
                    data = json.load(json_file)

                # Extract top-level keys from the JSON file to be the columns
                keys = list(data.keys())
                df = pd.DataFrame([{key: "" for key in keys}])

                # Write the DataFrame to a .tsv file
                df.to_csv(tsv_filepath, sep="\t", index=False)

            except Exception as e:
                print(f"Error processing file '{filename}': {e}")


dir = "/Users/isaacbevers/sensein/b2ai-wrapper/b2aiprep/src/b2aiprep/data\
    /b2ai-data-bids-like-template/phenotype"

make_tsv_files(dir)
