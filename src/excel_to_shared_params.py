import pandas as pd
import argparse
import os
import re
import random
import textwrap
from .naming_converter import convert_name


# --- Helper Functions ---


def infer_datatype(format_unit: str, value_set: str) -> str:
    """
    Infers the Revit Shared Parameter DATATYPE from Excel row data.
    """
    if not isinstance(format_unit, str):
        format_unit = ""
    if not isinstance(value_set, str):
        value_set = ""

    # Rule 1: Yes/No
    if "yes no" in value_set.lower().replace(",", ""):
        return "YESNO"

    # Rule 2: Specific Data Types based on Units
    # This list can be expanded with more specific units as needed
    # fmt: off
    unit_map = {
        'sqm': 'AREA', 'm2': 'AREA', 'mm2': 'AREA', 'm²': 'AREA', 'mm²': 'AREA',
        'm3': 'VOLUME', 'm³': 'VOLUME', 'l': 'VOLUME',
        'mm': 'LENGTH', 'm': 'LENGTH', 'cm': 'LENGTH',
        'kg': 'MASS_DENSITY', 'g': 'MASS_DENSITY',
        '°c': 'HVAC_TEMPERATURE',
        '°': 'ANGLE',
        '%': 'HVAC_FACTOR',
        'kn': 'FORCE',
        'va': 'ELECTRICAL_APPARENT_POWER',
        'w': 'ELECTRICAL_POWER',
        'v': 'ELECTRICAL_POTENTIAL', 'kv': 'ELECTRICAL_POTENTIAL', 'mv': 'ELECTRICAL_POTENTIAL',
        'a': 'ELECTRICAL_CURRENT', 'ma': 'ELECTRICAL_CURRENT',
        'hz': 'ELECTRICAL_FREQUENCY', 'ghz': 'ELECTRICAL_FREQUENCY',
        'lm': 'ELECTRICAL_LUMINOUS_FLUX',
        'cd/m²': 'ELECTRICAL_LUMINANCE',
        'lx': 'ELECTRICAL_ILLUMINANCE',
        'lm/w': 'ELECTRICAL_EFFICACY',
        'k': 'COLOR_TEMPERATURE',
        'url': 'URL' # Handle URL type
    }
    # fmt: on

    # Sort units by length descending to check for more specific units first (e.g. 'mm2' before 'm')
    sorted_units = sorted(unit_map.keys(), key=len, reverse=True)

    # Check for unit matches
    for unit in sorted_units:
        if unit in format_unit.lower().replace("n.a.", ""):
            return unit_map[unit]

    # Rule 3: Text for enumerated lists
    if format_unit == "n.a." and len(value_set.split(",")) > 1:
        return "TEXT"

    # Rule 4: Number for generic numeric formats
    if re.search(r"1E[-+]?\d+", format_unit, re.IGNORECASE):
        return "NUMBER"

    # Fallback to TEXT for strings or any other unhandled format
    return "TEXT"


def _clean(value: str) -> str:
    return re.sub("\s+", " ", value.strip())

def format_description(desc: str, value_set: str, examples: str) -> str:
    """
    Formats the description with enhanced logic for value sets and examples,
    ensuring it fits within Revit's 254-character limit.
    """
    # Clean up inputs
    base_desc = _clean(desc) if isinstance(desc, str) else ""
    value_set = _clean(value_set) if isinstance(value_set, str) else ""
    examples = _clean(examples) if isinstance(examples, str) else ""

    # If description is "Identical with name.", the description is primarily the name.
    if "identical with name" in base_desc.lower():
        base_desc = f""

    # Remove "Yes No" and "n.a." from value set
    if value_set.lower().replace(",", "") in ["yes no", "n.a", "n.a."]:
        value_set = ""

    final_desc = base_desc

    # Attempt to add the value set
    available_space = 254 - len(final_desc)
    if value_set and available_space > 5:
        value_set_str = f" i.e. {value_set}"
        if len((final_desc + value_set_str).strip()) <= 254:
            final_desc += value_set_str
        else:
            # Truncate value set at the last comma that fits
            truncated_values = value_set_str[:available_space]
            last_comma = truncated_values.rfind(',')
            # Ensure at least one full value is included after " i.e. "
            if last_comma > 5: 
                final_desc += truncated_values[:last_comma] + "…"

    # Attempt to add examples
    available_space = 254 - len(final_desc)
    if examples and available_space > 5:
        examples_str = f" e.g. {examples}"
        if len((final_desc + examples_str).strip()) <= 254:
            final_desc += examples_str
        else:
            # Truncate examples at the last word that fits
            last_space = len(textwrap.shorten(examples_str, width=available_space, placeholder="…"))
            if last_space > 5:
                final_desc += textwrap.shorten(examples_str, width=available_space, placeholder="…")


    # Final fallback truncation to ensure the limit is respected
    if len(final_desc) > 254:
        return final_desc[:253] + "…"

    return final_desc



# --- Main Processing Function ---


def create_shared_parameters_file(
    input_path: str, output_path: str, name_suffix: str, name_style: str
):
    """
    Reads a processed Excel file and generates a Revit Shared Parameter file.
    """
    print(f"Reading Excel file: {input_path}")

    try:
        xls = pd.ExcelFile(input_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'")
        return

    all_params = []
    groups = {}

    # --- Prepare Group and Parameter Data ---
    groups = {}
    parameters = []

    # Generate group IDs starting from a random base
    group_id_base = 200 + 10 * random.randint(0, 4)

    for i, sheet_name in enumerate(xls.sheet_names):
        group_id = group_id_base + i
        groups[sheet_name] = group_id

        print(f"  Processing sheet '{sheet_name}' as Group ID {group_id}...")
        df = pd.read_excel(xls, sheet_name=sheet_name)

        # Ensure required columns exist
        required_cols = [
            "MS-GUID",
            "Name",
            "Description",
            "Format, Unit",
            "Value set",
            "Examples",
        ]
        if not all(col in df.columns for col in required_cols):
            print(
                f"  - Warning: Sheet '{sheet_name}' is missing one or more required columns. Skipping."
            )
            continue

        for _, row in df.iterrows():
            # Skip rows with no GUID
            if pd.isna(row["MS-GUID"]):
                continue

            # 1. GUID
            guid = str(row["MS-GUID"]).replace("{", "").replace("}", "")

            # 2. Name
            param_name = convert_name(row["Name"], name_style) + name_suffix

            # 3. DataType
            param_type = infer_datatype(row["Format, Unit"], row["Value set"])

            # 4. Description
            description = format_description(row['Description'], row['Value set'], row['Examples'])

            param_line = (
                f"PARAM\t{guid}\t{param_name}\t{param_type}\t\t"
                f"{group_id}\t1\t{description}\t1\t0"
            )
            all_params.append(param_line)

    # --- Write to Shared Parameter File ---
    try:
        print(f"Writing to Shared Parameter file: {output_path}")
        with open(output_path, "w", encoding="utf-16-le") as f:
            # Header
            f.write("# This is a Revit shared parameter file.\n")
            f.write("# Do not edit manually.\n")
            f.write("*META\tVERSION\tMINVERSION\n")
            f.write("META\t2\t1\n")

            # Groups
            f.write("*GROUP\tID\tNAME\n")
            for name, group_id in groups.items():
                f.write(f"GROUP\t{group_id}\t{name}\n")

            # Parameters
            f.write(
                "*PARAM\tGUID\tNAME\tDATATYPE\tDATACATEGORY\tGROUP\tVISIBLE\tDESCRIPTION\tUSERMODIFIABLE\tHIDEWHENNOVALUE\n"
            )
            for line in all_params:
                f.write(line + "\n")
        print("Successfully created Revit Shared Parameters file.")

    except Exception as e:
        print(f"\nError writing to file: {e}")


# --- Command-line entry point ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts a cleaned Excel file into a Revit Shared Parameters file."
    )
    parser.add_argument(
        "input_file",
        help="Path to the source Excel file (.xlsx).",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="Path for the output .txt Shared Parameter file. Defaults to '[input]_shared_params.txt'.",
    )
    parser.add_argument(
        "-n",
        "--name-style",
        help="The naming style for the parameter names.",
        choices=[
            "title",
            "capitalise",
            "camel",
            "pascal",
            "snake",
            "pascal_snake",
            "allcaps",
        ],
        default="pascal",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        help="A suffix to append to every parameter name.",
        default="",
    )
    args = parser.parse_args()

    output_path = (
        args.output_file
        if args.output_file
        else f"{os.path.splitext(args.input_file)[0]}_shared_params.txt"
    )

    # Run the main function
    try:
        create_shared_parameters_file(
            args.input_file, output_path, args.suffix, args.name_style
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
