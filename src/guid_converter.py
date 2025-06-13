# import base64
# import uuid
import re
from . import ifcopenshell_guid as ifc_guid


def process_and_convert_guid(multiline_guid: str) -> tuple[str | None, str | None]:
    """
    Processes a short IFC-GUID string that may be split over multiple lines,
    cleans it, and returns the corrected short GUID and its expanded long version.

    This function uses the official IfcOpenShell algorithm for conversion.

    Args:
        multiline_guid: A string containing a short GUID, potentially with
                        line breaks and formatting artifacts like hyphens.

    Returns:
        A tuple containing (corrected_short_guid, long_guid).
        Returns (None, None) if the input cannot be resolved into a valid GUID.
    """
    if not multiline_guid or not isinstance(multiline_guid, str):
        return None, None

    # Clean the string: remove all whitespace and hyphens.
    # In the IFC-GUID format, these are never legitimate characters.
    cleaned_guid = re.sub(r"[\s-]", "", multiline_guid)

    # A valid IFC-GUID is exactly 22 characters long.
    if len(cleaned_guid) != 22:
        return None, None

    try:
        # Use the official 'expand' function for conversion
        long_guid = ifc_guid.expand(cleaned_guid)
        return ifc_guid.compress(long_guid), ifc_guid.split(long_guid)
    except Exception:
        # The cleaned string was still not a valid IFC-GUID
        return None, None
