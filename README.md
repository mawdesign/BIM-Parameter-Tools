# BIM Parameter Tools
A collection of open-source Python tools designed to simplify the management, conversion, and translation of BIM parameters across 
different software platforms like Revit and IFC.

## Project Goal
The world of BIM involves multiple software platforms, each with its own way of storing and identifying data. Managing parameters—
especially GUIDs, naming conventions, and shared parameter files—between these platforms can be a manual and error-prone process.

This repository aims to provide a robust suite of command-line and scriptable tools to automate these conversions, saving time and 
improving data consistency for BIM managers, coordinators, and developers.

## Features & Roadmap
### Current Features
* **IFC Short GUID to Revit Long GUID Converter:**
  * A Python function that intelligently converts the compressed, URL-safe Base64 GUID format used by IFC into the standard 32-digit
    hexadecimal GUID format required for Revit Shared Parameter files.
  * Automatically handles formatting artifacts, such as hyphens or underscores inserted by document software during line wrapping.

### Planned Features (Roadmap)
We welcome contributions to help build out the following tools:

* [ ] **Long GUID to Short GUID Converter:** A tool to perform the reverse conversion, from a standard Revit GUID to a compressed
      IFC-style GUID.
* [ ] **Excel to Revit Shared Parameter File Generator:** A script to convert a standardized Excel template of parameter definitions
      into a valid Revit Shared Parameter .txt file.
* [ ] **Parameter Naming Convention Converter:** A flexible tool to batch-convert parameter names between common conventions (e.g.,
      `Title Case` to `snake_case` or `camelCase`) and manage prefixes and suffixes.
* [ ] **Parameter Language Translator:** A utility to facilitate translating parameter names between different languages using a
      predefined translation map or service.

## Getting Started
### Prerequisites
* Python 3.8 or higher

### Installation
1. **Clone the repository:**
```bash
git clone https://github.com/your-username/bim-parameter-tools.git
cd bim-parameter-tools
```
1. **Set up a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
1. **Install the required packages:**
The project has minimal dependencies. Currently the only package needed is `pytest` for running the tests.
```bash
pip install -r requirements.txt
```

## Usage
### GUID Converter
The primary function for GUID conversion is `process_and_convert_guid` located in the `guid_converter.py` 
script. It is designed to handle short GUIDs that have been split across two lines in a document.

### Example:
```python
from guid_converter import process_and_convert_guid

# Example short GUID that was split with a hyphen by document software
multiline_guid = """OjUoLaQbSJa-
LY55KONd1nQ"""

# Process the string to get the corrected short GUID and the expanded long GUID
short_guid, long_guid = process_and_convert_guid(multiline_guid)

if long_guid:
    print(f"Corrected Short GUID: {short_guid}")
    print(f"Expanded Long GUID:   {long_guid}")
else:
    print("Could not convert the provided string into a valid GUID.")

# Expected Output:
# Corrected Short GUID: OjUoLaQbSJaLY55KONd1nQ
# Expanded Long GUID:   3a35282d-a41b-4896-8b63-9e4a38d7759d
```

## Testing
The project includes a test suite to ensure the reliability of the tools. To run the tests, navigate 
to the root directory of the project and run `pytest`.
```bash
pytest
```
You should see a report indicating that all tests have passed.

## Contributing
Contributions are welcome and greatly appreciated! This project is intended to be a community-driven resource.

If you would like to contribute, please follow these steps:
1. **Fork the repository**.
1. **Create a new branch** for your feature or bug fix (`git checkout -b feature/AmazingNewTool`).
1. **Write your code**. Please include tests for any new functionality.
1. **Ensure all tests pass** by running `pytest`.
1. **Submit a pull request** with a clear description of your changes.

By contributing, you agree that your submissions will be licensed under the CC0 1.0 Universal license.

## License
This project is dedicated to the public domain. All code and documentation are released under the [Creative Commons Zero (CC0) v1.0 Universal license](LICENSE). 
You are free to copy, modify, distribute, and use the work, even for commercial purposes, without any restrictions.
