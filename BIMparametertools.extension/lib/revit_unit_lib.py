# -*- coding: utf-8 -*-
"""
BIM Parameter Tools - Revit Unit and Spec Library

This module contains reusable functions for querying unit and specification
data from the Revit API. It is designed to be imported by other scripts
within the pyRevit extension to provide a consistent data source.
"""
# ------------------------------------------------------------------------------
# Preamble
# ------------------------------------------------------------------------------
__author__ = "BIM Parameter Tools Contributor"

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
# Import necessary components from the Revit API.
# These are available in the pyRevit environment.
from Autodesk.Revit.DB import UnitUtils, LabelUtils, ForgeTypeId, FormatOptions
from pyrevit import script, HOST_APP

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
            if HOST_APP.is_exactly(2021):
                spec_discipline = UnitUtils.GetUnitGroup(spec_id)
            elif HOST_APP.is_newer_than(2021):
                spec_discipline = UnitUtils.GetDiscipline(spec_id)
            else:
                spec_discipline = ""

            spec_data = {
                "Name": LabelUtils.GetLabelForSpec(spec_id),
                "TypeCatalogName": UnitUtils.GetTypeCatalogStringForSpec(spec_id),
                "ForgeTypeId": spec_id.TypeId,
                "Discipline": spec_discipline.ToString(),
                "ValidUnits": valid_unit_ids,
            }
            all_specs.append(spec_data)
        except Exception as e:
            logger.warning("Could not process spec: {}. Error: {}".format(spec_id.TypeId, e))
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
            logger.warning("Could not process unit: {}. Error: {}".format(unit_id.TypeId, e))
            continue
            
    logger.debug("Finished processing {} unique units.".format(len(all_units_map)))
    return all_units_map


