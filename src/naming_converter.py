import re

# Skip Black format for these to maintain clarity
# fmt: off
# Words to be kept lowercase in CMOS Title Case, unless they are the first or last word.
CMOS_MINOR_WORDS = {
    'a', 'an', 'the',  # Articles
    'and', 'but', 'for', 'or', 'nor',  # Coordinating Conjunctions
    'as', 'at', 'by', 'for', 'in', 'of', 'off', 'on', 'per', 'to', 'up', 'via'  # Short Prepositions
}

# Units of measurement to be excluded from ALL CAPS conversion.
# Using a set for efficient lookup.
UNITS_TO_PRESERVE = {
    'mm', 'cm', 'm', 'km', 'nm'   # Metric length
    'sqm', 'm2', 'm²', 'm3', 'm³', 'l' # Area and Volume
    'mA', 'Ah', 'mV', 'kV', 'VA', # Electrical
    's', 'µs', 'h', 'Hz', 'GHz',  # Time and frequency
    'g', 'kg',                    # Metric mass
    'lm', 'cd/m²', 'lx',          # Lighting
    'dB', 'dBm', 'dBA',           # Acoustics
    'kN',                         # Force
}
# fmt: on


def _get_words(name_string: str) -> list[str]:
    """
    Splits a string into a list of words, preserving abbreviations.
    Example: "ifcWall_and_hvacSystem" -> ["ifc", "Wall", "and", "hvac", "System"]
    """
    if not name_string:
        return []
    # This regex finds:
    # 1. Abbreviations (2+ uppercase letters) OR
    # 2. Alphanumeric words (letters and numbers combined)
    return re.findall(r'[A-Z]{2,}|[a-zA-Z0-9]+', name_string)


def to_title_case_cmos(name_string: str) -> str:
    """Converts a string to Title Case following Chicago Manual of Style."""
    words = _get_words(name_string)
    if not words:
        return ""

    cased_words = []
    for i, word in enumerate(words):
        lower_word = word.lower()
        if word.isupper():
            cased_words.append(word)
        elif i == 0 or i == len(words) - 1 or lower_word not in CMOS_MINOR_WORDS:
            cased_words.append(word.capitalize())
        else:
            cased_words.append(lower_word)
    return " ".join(cased_words)


def to_capitalise_all_words(name_string: str) -> str:
    """Converts a string to have every word capitalized."""
    words = _get_words(name_string)
    return " ".join([word if word.isupper() else word.capitalize() for word in words])


def to_all_caps(name_string: str) -> str:
    """Converts a string to ALL CAPS, preserving specified units in lowercase."""
    words = _get_words(name_string)
    if not words:
        return ""

    cased_words = []
    # Regex to detect a number (int or float) followed by a unit from the set
    unit_pattern_str = (
        r"^\d+(\.\d+)?("
        + "|".join(re.escape(unit) for unit in UNITS_TO_PRESERVE)
        + r")$"
    )
    unit_pattern = re.compile(unit_pattern_str, re.IGNORECASE)

    for word in words:
        # Check if the word itself is a unit or if it's a number-unit combo
        if word in UNITS_TO_PRESERVE or unit_pattern.match(word):
            cased_words.append(word)  # Preserve original case of the unit/word
        else:
            cased_words.append(word.upper())  # Otherwise, convert to uppercase

    return " ".join(cased_words)


def to_snake_case(name_string: str, upper: bool = False) -> str:
    """Converts a string to snake_case or Snake_Case (Pascal_Case)."""
    words = _get_words(name_string)
    if upper:
        return "_".join([word.capitalize() for word in words])
    return "_".join([word.lower() for word in words])


def to_camel_case(name_string: str, upper: bool = False) -> str:
    """Converts a string to camelCase or PascalCase (UpperCamelCase)."""
    words = _get_words(name_string)
    if not words:
        return ""

    if upper:
        first_word = words[0] if words[0].isupper() else words[0].capitalize()
    else:
        first_word = words[0] if words[0].isupper() else words[0].lower()
    rest_words = [word if word.isupper() else word.capitalize() for word in words[1:]]
    return "".join([first_word] + rest_words)


def convert_name(name_string: str, style: str) -> str:
    """
    Main dispatcher function to convert a string to a specified naming style.
    """
    if not isinstance(name_string, str):
        return ""

    style_map = {
        "title": to_title_case_cmos,
        "capitalise": to_capitalise_all_words,
        "allcaps": to_all_caps,
        "camel": lambda s: to_camel_case(s, upper=False),
        "pascal": lambda s: to_camel_case(s, upper=True),
        "snake": lambda s: to_snake_case(s, upper=False),
        "pascal_snake": lambda s: to_snake_case(s, upper=True),
    }
    conversion_func = style_map.get(style.lower())
    return conversion_func(name_string) if conversion_func else name_string
