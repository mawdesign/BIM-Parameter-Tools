import pandas as pd
import argparse
import os
import re
from .guid_converter import process_and_convert_guid


def analyze_name_column(df: pd.DataFrame, sheet_name: str):
    """Analyzes the 'Name' column for naming convention issues and prints warnings."""
    print(f"    - Analyzing 'Name' column for sheet '{sheet_name}'...")
    name_col = df['Name']
    # Check if an 'ID' column exists to use for logging
    has_id_column = 'ID' in df.columns

    for index, name in name_col.dropna().items():
        if not isinstance(name, str):
            continue

        # Determine the identifier for the row (ID value or Row number)
        if has_id_column:
            identifier = df.loc[index, 'ID']
            identifier_str = f"ID: {identifier}"
        else:
            identifier_str = f"Row {index + 2}"
        
        # Find words that are likely capitalized abbreviations (e.g., IFC, HVAC)
        abbreviations = re.findall(r'\b[A-Z]{2,}\b', name)
        if abbreviations:
            print(f"      - Info: Found potential abbreviation(s) {abbreviations} in '{name}' ({identifier_str})")
            
        # Find words with improper capitalization (e.g., 'TitleCase')
        improper_caps = re.findall(r'\b[A-Z][a-z]+\b', name)
        if improper_caps:
             print(f"      - Warning: Found improper capitalization in '{name}' ({identifier_str}). Words: {improper_caps}")


def clean_name_column(name_series: pd.Series) -> pd.Series:
    """Cleans the 'Name' column by handling multi-line entries."""
    def clean_name(name):
        if not isinstance(name, str):
            return name
        # First, remove hyphens followed by a newline
        name = re.sub(r'-\n', '', name)
        # Then, replace any remaining newlines with a space
        name = name.replace('\n', ' ')
        return name
        
    return name_series.apply(clean_name)


def process_excel_file(input_path: str, output_path: str):
    """
    Opens an Excel file, processes GUIDs in each sheet, and saves a new file.

    For each sheet, it looks for a "GUID" column, processes each entry using
    the guid_converter, and adds "IFC-GUID" and "MS-GUID" columns.
    All other data is copied as is.

    Args:
        input_path (str): The path to the source Excel file.
        output_path (str): The path where the new Excel file will be saved.
    """
    print(f"Opening input file: {input_path}")

    # Use pandas ExcelWriter to be able to write multiple sheets
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        # Load the entire Excel file to get access to all sheets
        input_xls = pd.ExcelFile(input_path)

        print(f"Found sheets: {', '.join(input_xls.sheet_names)}")

        for sheet_name in input_xls.sheet_names:
            print(f"  Processing sheet: '{sheet_name}'...")

            # Read the current sheet into a DataFrame
            df = pd.read_excel(input_xls, sheet_name=sheet_name)

            # --- Name Column Processing (Analyze first, then clean) ---
            if 'Name' in df.columns:
                analyze_name_column(df, sheet_name)
                df['Name'] = clean_name_column(df['Name'])
                print("    - Cleaned 'Name' column.")

            # --- GUID Column Processing ---
            if "GUID" not in df.columns:
                print(
                    f"    - Warning: 'GUID' column not found in sheet '{sheet_name}'. Copying sheet as is."
                )
                # If no GUID column, write the original DataFrame and move to the next sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                continue

            # This helper function handles non-string or empty cells gracefully
            def safe_convert(guid_str):
                if isinstance(guid_str, str) and guid_str.strip():
                    return process_and_convert_guid(guid_str)
                # Return a tuple of Nones for empty/invalid cells
                return (None, None)

            # Apply the conversion function to the 'GUID' column.
            # This creates a Series of tuples: [(short1, long1), (short2, long2), ...]
            results = df["GUID"].apply(safe_convert)

            # Create the two new columns by splitting the tuples in the results Series
            df["IFC-GUID"] = results.str[0]
            df["MS-GUID"] = results.str[1]
            print(f"    - Successfully processed GUIDs and created new columns.")

            # --- Reorder and Finalize Columns ---
            # Drop the original GUID column
            df.drop(columns=['GUID'], inplace=True)

            # Create the desired column order
            existing_cols = df.columns.tolist()
            # Remove the new GUID columns to append them at the front
            for col in ['IFC-GUID', 'MS-GUID']:
                if col in existing_cols:
                    existing_cols.remove(col)

            final_col_order = ['IFC-GUID', 'MS-GUID'] + existing_cols
            df = df[final_col_order]

            # Write the modified DataFrame to the new Excel file
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\nProcessing complete. New file saved at: {output_path}")


if __name__ == "__main__":
    # Set up argument parser for command-line usage
    parser = argparse.ArgumentParser(
        description="A tool to process IFC-GUIDs within an Excel file. It converts short, multi-line GUIDs "
        "into corrected short and expanded long formats in new columns."
        "Refer to https://technical.buildingsmart.org/resources/ifcimplementationguidance/ifc-guid/"
    )
    parser.add_argument(
        "input_file",
        help="The path to the source Excel file (.xlsx).",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="The path for the processed Excel file. Defaults to '[input]_converted.xlsx'.",
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found at '{args.input_file}'")
        exit()
    elif not args.input_file.lower().endswith(".xlsx"):
        print(f"Error: Input file must be a .xlsx file.")
        exit()

    # Determine and validate output file path
    if args.output_file:
        output_path = args.output_file
    else:
        # Create a default output filename if none is provided
        base, ext = os.path.splitext(args.input_file)
        output_path = f"{base}_converted{ext}"

    if not output_path.lower().endswith(".xlsx"):
        print(
            f"Error: Output file path must be a .xlsx file. Path provided: '{output_path}'"
        )
        exit()

    # Check for overwrite
    if os.path.exists(output_path):
        try:
            # Ask the user for confirmation to overwrite
            overwrite_choice = (
                input(f"Output file '{output_path}' already exists. Overwrite? (y/n): ")
                .lower()
                .strip()
            )
            if overwrite_choice != "y":
                print("Operation cancelled.")
                exit()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            exit()

    # Process the file
    try:
        process_excel_file(args.input_file, output_path)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
