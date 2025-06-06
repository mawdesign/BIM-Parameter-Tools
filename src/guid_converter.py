import base64
import uuid
import re

def _try_decode_guid(short_guid: str) -> str | None:
    """
    Internal helper function to attempt decoding a potential short GUID.
    A valid short GUID for a 16-byte UUID will have a length that,
    when padded to a multiple of 4, decodes to exactly 16 bytes.
    """
    try:
        # Calculate required padding
        padding = '=' * (-len(short_guid) % 4)
        padded_guid = short_guid + padding
        
        # Decode using URL-safe alphabet, which handles '-' and '_'
        decoded_bytes = base64.urlsafe_b64decode(padded_guid)
        
        # A valid GUID must be 16 bytes (128 bits)
        if len(decoded_bytes) == 16:
            # Convert bytes to a standard long GUID string
            long_guid = str(uuid.UUID(bytes=decoded_bytes))
            return long_guid
    except (ValueError, base64.binascii.Error):
        # The string is not valid Base64 or has incorrect padding
        return None
    return None

def process_and_convert_guid(multiline_guid: str) -> tuple[str | None, str | None]:
    """
    Processes a short GUID string that is split over two lines,
    determines if the hyphen/underscore at the split is legitimate,
    and returns the corrected short GUID and its long version.

    Args:
        multiline_guid: A string containing a short GUID split by a newline,
                        often with a hyphen or underscore before the newline.

    Returns:
        A tuple containing (corrected_short_guid, long_guid).
        Returns (None, None) if the input cannot be resolved into a valid GUID.
    """
    if not multiline_guid or '\n' not in multiline_guid:
        # Handle empty or single-line strings as invalid for this function's purpose
        return None, None

    # Clean up leading/trailing whitespace from the whole block
    clean_guid = multiline_guid.strip()
    
    # --- Hypothesis 1: The hyphen/underscore at the break is an ARTIFACT ---
    attempt1_removed = re.sub(r'[-_]\n', '', clean_guid)

    if len(attempt1_removed) == 22:
        long_guid = _try_decode_guid(attempt1_removed)
        if long_guid:
            return attempt1_removed, long_guid
            
    # --- Hypothesis 2: The hyphen/underscore at the break is LEGITIMATE ---
    attempt2_kept = clean_guid.replace('\n', '')
    
    long_guid_kept = _try_decode_guid(attempt2_kept)
    if long_guid_kept:
        return attempt2_kept, long_guid_kept
        
    # --- Last Chance for Hypothesis 1 if it wasn't 22 chars ---
    if len(attempt1_removed) != 22:
        long_guid_removed = _try_decode_guid(attempt1_removed)
        if long_guid_removed:
            return attempt1_removed, long_guid_removed

    # If both hypotheses fail, the GUID is likely corrupt.
    return None, None
