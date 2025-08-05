# -*- coding: utf-8 -*-
"""
BIM Parameter Tools - Revit Unit and Spec Library

This module contains reusable functions for querying unit and specification
data from the Revit API. It is designed to be imported by other scripts
within the pyRevit extension to provide a consistent data source.
"""

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# Import necessary components from the Revit API.
# These are available in the pyRevit environment.
from Autodesk.Revit.DB import (
    UnitUtils,
    LabelUtils,
    ForgeTypeId,
    FormatOptions,
    SpecTypeId,
)
from pyrevit import script, HOST_APP


# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

# Defines the seven base SI quantities to prioritize them in sorted lists.
BASE_QUANTITY_SPECS = [
    SpecTypeId.Length.TypeId,
    SpecTypeId.Angle.TypeId,
    SpecTypeId.Mass.TypeId,
    SpecTypeId.Time.TypeId,
    SpecTypeId.Current.TypeId,
    SpecTypeId.ElectricalTemperature.TypeId,
    SpecTypeId.LuminousIntensity.TypeId,
]

# ------------------------------------------------------------------------------
# Core Data Enumeration Function
# ------------------------------------------------------------------------------


def get_revit_specs():
    """
    Enumerates all measurable specifications from the Revit API.

    This function iterates through all specs (like Length, Area, etc.) and
    compiles a list of their properties, including which units are valid for them.

    Returns:
        list: A list of dictionaries, where each dictionary represents one spec.
    """
    logger = script.get_logger()
    logger.debug("Gathering all measurable specifications from Revit...")

    all_specs = []
    spec_ids = UnitUtils.GetAllSpecs()

    for spec_id in spec_ids:
        try:
            # For each spec, get its valid units and store their ForgeTypeId strings
            valid_unit_ids = [unit.TypeId for unit in UnitUtils.GetValidUnits(spec_id)]

            # Handle API changes for retrieving Discipline between Revit versions
            if HOST_APP.is_exactly(2021):
                spec_discipline = UnitUtils.GetUnitGroup(spec_id).ToString()
            elif HOST_APP.is_newer_than(2021):
                spec_discipline = LabelUtils.GetLabelForDiscipline(
                                    UnitUtils.GetDiscipline(spec_id)
                                    )
            else:
                spec_discipline = ""  # Fallback for older versions

            spec_data = {
                "Name": LabelUtils.GetLabelForSpec(spec_id),
                "TypeCatalogName": UnitUtils.GetTypeCatalogStringForSpec(spec_id),
                "ForgeTypeId": spec_id.TypeId,
                "Discipline": spec_discipline,
                "ValidUnits": valid_unit_ids,
            }
            all_specs.append(spec_data)
        except Exception as e:
            logger.warning(
                "Could not process spec: {}. Error: {}".format(spec_id.TypeId, e)
            )
            continue

    logger.debug("Finished processing {} specifications.".format(len(all_specs)))
    return all_specs


def get_revit_units():
    """
    Enumerates all unique units available in the Revit API.

    Returns:
        dict: A dictionary of all unique units, keyed by their ForgeTypeId.
    """
    logger = script.get_logger()
    logger.debug("Gathering all unique units from Revit...")

    all_units_map = {}
    unit_ids = UnitUtils.GetAllUnits()

    for unit_id in unit_ids:
        try:
            unit_urn = unit_id.TypeId

            # Get all possible symbols (abbreviations) for this unit
            unit_symbols = []
            symbol_ids = FormatOptions.GetValidSymbols(unit_id)
            for symbol_id in symbol_ids:
                # Some symbols might be empty, so we check first
                if symbol_id and not symbol_id.Empty():
                    unit_symbols.append(LabelUtils.GetLabelForSymbol(symbol_id))

            # Store all relevant data about the unit, keyed by its unique ForgeTypeId
            all_units_map[unit_urn] = {
                "TypeCatalogName": UnitUtils.GetTypeCatalogStringForUnit(unit_id),
                "UnitName": LabelUtils.GetLabelForUnit(unit_id),
                "UnitSymbols": unit_symbols,
            }
        except Exception as e:
            logger.warning(
                "Could not process unit: {}. Error: {}".format(unit_id.TypeId, e)
            )
            continue

    logger.debug("Finished processing {} unique units.".format(len(all_units_map)))
    return all_units_map


def create_reverse_unit_lookup(specs_data, units_data):
    """
    Creates a reverse lookup dictionary mapping unit symbols (e.g., "mm")
    to a list of all valid (spec, unit) tuples where that symbol can be used.

    The resulting list for each symbol is sorted according to a specific
    hierarchy to present the most relevant options first.

    Args:
        specs_data (list): The list of spec dictionaries from get_revit_specs().
        units_data (dict): The dictionary of unit data from get_revit_units().

    Returns:
        dict: A dictionary where keys are unit symbols and values are sorted
              lists of (spec_forge_type_id, unit_forge_type_id) tuples.
    """
    logger = script.get_logger()
    logger.debug("Creating reverse lookup index for unit symbols...")
    reverse_lookup = {}

    # Create a quick lookup map from spec ForgeTypeId to the spec's discipline
    spec_discipline_map = {
        spec["ForgeTypeId"]: spec["Discipline"] for spec in specs_data
    }

    # Create a unique, sorted list of all disciplines (excluding 'Common') for stable sorting
    other_disciplines = sorted(
        list(set(d for d in spec_discipline_map.values() if d and d != "Common"))
    )

    # Step 1: Build the initial reverse lookup map
    for unit_urn, unit_info in units_data.items():
        for symbol in unit_info.get("UnitSymbols", []):
            if symbol not in reverse_lookup:
                reverse_lookup[symbol] = []

            # Find all specs that use this unit
            for spec in specs_data:
                if unit_urn in spec.get("ValidUnits", []):
                    spec_urn = spec["ForgeTypeId"]
                    reverse_lookup[symbol].append((spec_urn, unit_urn))

    logger.debug("Sorting the reverse lookup index...")
    # Step 2: Sort the lists for each symbol according to the specified hierarchy
    for symbol, spec_unit_pairs in reverse_lookup.items():

        def sort_key(pair):
            spec_id, _ = pair
            discipline = spec_discipline_map.get(spec_id)

            # Priority 1: Base Quantities
            if spec_id in BASE_QUANTITY_SPECS:
                return (BASE_QUANTITY_SPECS.index(spec_id), discipline, spec_id)
            # Priority 2: Common Discipline
            elif discipline == "Common":
                return (100, discipline, spec_id)
            # Priority 3: All other disciplines, sorted alphabetically
            else:
                return (101 + other_disciplines.index(discipline), discipline, spec_id)

        spec_unit_pairs.sort(key=sort_key)

    logger.debug("Finished creating reverse lookup index.")
    return reverse_lookup
