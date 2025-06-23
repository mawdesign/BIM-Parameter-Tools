# -*- coding: utf-8 -*-
"""
BIM Parameter Tools - Enumerate Revit ForgeTypeIds

This script acts as the user interface for enumerating Revit specifications.
It calls the core logic from the shared library (revit_unit_lib.py) and
handles saving the resulting normalized JSON data to a file, including
metadata about the Revit environment.

The script prompts the user to save the output as a JSON file, which can then
be used as a foundational mapping table for unit and data type conversions
between different standards (e.g., ISO, IFC, Autodesk).
"""
# ------------------------------------------------------------------------------
# Preamble
# ------------------------------------------------------------------------------
__title__ = "Enumerate Specs"
__author__ = "MAW"
__doc__ = "Exports a complete list of Revit's ForgeTypeId specifications to a JSON file."

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# Import necessary components from the shared library
from revit_unit_lib import get_revit_specs, get_revit_units

# Import pyRevit forms for user interaction (file save dialog)
from pyrevit import forms, script, HOST_APP

# Import Python standard libraries for file handling
import json
import os
import io
from datetime import datetime

# ------------------------------------------------------------------------------
# Main Script Logic
# ------------------------------------------------------------------------------

def main():
    """
    Main function to get all specs and units, add metadata, and save to a
    user-selected JSON file.
    """
    logger = script.get_logger()

    # 1. Prompt user to select a location to save the JSON file.
    save_path = forms.save_file(
        title="Save Specs & Units JSON file",
        default_name="RevitUnitSpecMap.json",
        file_ext="json",
    )

    # 2. If the user cancelled the dialog, exit the script gracefully.
    if not save_path:
        logger.info("Operation cancelled by user.")
        return

    # 3. Call the library functions to get the normalized data.
    try:
        specs_data = get_revit_specs()
        units_data = get_revit_units()
    except Exception as e:
        forms.alert("Failed to gather data from Revit API.\nError: {}".format(e), exitscript=True)
        return

    # 4. Prepare the final output dictionary, including metadata.
    output_data = {
        "meta": {
            "retrieval_date": datetime.now().isoformat(),
            "revit_version": HOST_APP.version,
            "revit_version_name": HOST_APP.version_name,
            "revit_build": HOST_APP.app.VersionBuild,
            "comment": "This file contains a normalized map of specifications and units as enumerated from the Revit API."
        },
        "specs": specs_data,
        "units": units_data
    }

    # 5. Write the collected data to the selected JSON file.
    try:
        with io.open(save_path, "w", encoding="utf-8") as json_file:
            # json.dump writes the Python dictionary to the file.
            # 'indent=2' makes the output file human-readable.
            # We ensure non-ASCII characters are written correctly.
            data = json.dumps(output_data, indent=2, ensure_ascii=False)
            json_file.write(data)

        logger.debug("Successfully wrote data to: {}".format(save_path))

        # 6. Inform the user that the process is complete.
        forms.alert(
            "Successfully exported {} specifications and {} unique units to:\n\n{}".format(
                len(specs_data),
                len(units_data),
                os.path.basename(save_path)
            ),
            title="Export Complete"
        )
    except IOError as e:
        # If the file can't be written (e.g., permissions issue), inform the user.
        logger.warning("Error writing to file: {}".format(e))
        forms.alert(
            "Could not save the file to the selected path.\n\nPlease check file permissions.\nError: {}".format(e),
            title="File Write Error"
        )

# ------------------------------------------------------------------------------
# Script Execution
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
