import glob
import importlib.resources as pkg_resources
import json
import os
import shutil
from typing import Dict, List, Optional

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


def copy_package_resource(
    package: str, resource: str, destination_dir: str, destination_name: str = None
) -> None:
    """
    Copy a file or directory from within a package to a specified directory.

    Args:
        package (str): The package name where the file or directory is located.
        resource (str): The resource name (file or directory path within the package).
        destination_dir (str): The directory where the file or directory should be copied.
        destination_name (str, optional): The new name for the copied file or directory.
        If not provided, the original name is used.

    Returns:
        None
    """
    if destination_name is None:
        destination_name = os.path.basename(resource)
    destination_path = os.path.join(destination_dir, destination_name)
    with pkg_resources.path(package, resource) as src_path:
        src_path = str(src_path)  # Convert to string to avoid issues with path-like objects
        if os.path.isdir(src_path):  # Check if the resource is a directory
            shutil.copytree(src_path, destination_path)
        else:  # Otherwise, assume it is a file
            shutil.copy(src_path, destination_path)


def remove_files_by_pattern(directory: str, pattern: str) -> None:
    """
    Remove all files in a given directory that match a specific pattern.

    Args:
        directory (str): The path to the directory.
        pattern (str): The pattern to match files (e.g., "*.txt" for all text files).

    Returns:
        None
    """
    # Construct the full path pattern
    path_pattern = os.path.join(directory, pattern)

    # Use glob to find all files that match the pattern
    files_to_remove = glob.glob(path_pattern)

    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")


def construct_tsv_from_json(
    df: pd.DataFrame, json_file_path: str, output_dir: str, output_file_name: Optional[str] = None
) -> None:
    """
    Constructs a TSV file from a DataFrame and a JSON file specifying column labels.
    Combines entries so that there is one row per record_id.

    Args:
        df (pd.DataFrame): DataFrame containing the data.
        json_file_path (str): Path to the JSON file with the column labels.
        output_dir (str): Output directory where the TSV file will be saved.
        output_file_name (str, optional): The name of the output TSV file.
                                          If not provided, the JSON file name is used with a .tsv extension.

    Returns:
        None: This function does not return a value; it writes the output to a TSV file.
    """
    # Load the column labels from the JSON file
    with open(json_file_path, "r") as f:
        json_data = json.load(f)

    # Extract column names from the JSON file
    column_labels = list(json_data.keys())

    # Filter column labels to only include those that exist in the DataFrame
    valid_columns = [col for col in column_labels if col in df.columns]

    if not valid_columns:
        raise ValueError("No valid columns found in DataFrame that match JSON file")

    # Select the relevant columns from the DataFrame
    selected_df = df[valid_columns]

    # Combine entries so there is one row per record_id
    combined_df = selected_df.groupby("record_id").first().reset_index()

    # Define the output file name and path
    if output_file_name is None:
        output_file_name = os.path.splitext(os.path.basename(json_file_path))[0] + ".tsv"

    tsv_path = os.path.join(output_dir, output_file_name)

    # Save the combined DataFrame to a TSV file
    combined_df.to_csv(tsv_path, sep="\t", index=False)

    print(f"TSV file created and saved to: {tsv_path}")
