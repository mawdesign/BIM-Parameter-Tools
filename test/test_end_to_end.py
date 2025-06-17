import pytest
import pandas as pd
import os
import subprocess

# --- Test Data and Configuration ---

# This dictionary represents the minimal Excel data needed for testing.
SAMPLE_DATA = {
    "General": pd.DataFrame(
        {
            "ID": ["GEN-01", "GEN-02", "GEN-03"],
            "Name": ["overall diameter", "luminaire housing shape 3D", "silicon-free"],
            "GUID": [
                "2GZ1YB8enFVhDHOKgLc$BU",
                "1zs4Cj96j3d8TWA-\neeixJga",
                "3jAmXEFTn9oPlBD_oO4BfE",
            ],
            "Description": [
                "Overall diameter of the housing of a round luminaire.",
                "A very long description that will most definitely need to be truncated at a word break to fit within the 254 character limit that is imposed by the Revit shared parameter file format itself. This ensures the shortening logic works as expected.",
                "Identical with name.",
            ],
            "Format, Unit": ["1E0, mm", "n.a.", "n.a."],
            "Value set": ["n.a.", "Cylinder, Cuboid, Cube, Sphere", "Yes, No"],
            "Examples": ["200", "", ""],
        }
    ),
    "Electrical": pd.DataFrame(
        {
            "ID": ["ELEC-01", "ELEC-02", "ELEC-03"],
            "Name": ["apparent power", "light source included", "windage"],
            "GUID": [
                "2FA0ih18LF_uKt46e5ErIv",
                "018C_3ZRn5IufwY89oB9NV",
                "2lRl_DnFf97P6CAO2kfYEp",
            ],
            "Description": [
                "Apparent Power of the product.",
                "Identical with name.",
                "Projected area used to calculate wind resistance.",
            ],
            "Format, Unit": ["1E0, VA", "n.a.", "1E-2, m²"],
            "Value set": ["n.a.", "Yes, No", "n.a."],
            "Examples": ["12.5", "Yes", "0.75"],
        }
    ),
}

# --- Pytest Fixture for Test File Management ---


@pytest.fixture
def setup_test_files(tmp_path):
    """
    This fixture creates a temporary directory structure with a sample Excel file
    and yields the paths for the test to use. It handles cleanup automatically.
    """
    # Create temporary directories
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Define file paths
    source_excel_path = data_dir / "sample_parameters.xlsx"
    cleaned_excel_path = output_dir / "sample_parameters_cleaned.xlsx"
    final_sp_path = output_dir / "revit_shared_params.txt"

    # Create the sample Excel file from our data dictionary
    with pd.ExcelWriter(source_excel_path) as writer:
        for sheet_name, df in SAMPLE_DATA.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Yield the paths to the test function
    yield {
        "source": str(source_excel_path),
        "cleaned": str(cleaned_excel_path),
        "final_sp": str(final_sp_path),
    }

    # Pytest handles cleanup of tmp_path after the test completes


# --- The End-to-End Test Function ---


def test_full_conversion_workflow(setup_test_files):
    """
    This test executes the full data processing pipeline:
    1. Runs excel_guid_processor.py to clean the source Excel file.
    2. Runs excel_to_shared_params.py to generate the Revit SP file.
    3. Validates the content of the final .txt file.
    """
    paths = setup_test_files

    # --- Step 1: Run the first script (GUID and Name cleaning) ---
    cmd1 = [
        "python",
        "-m",
        "src.excel_guid_processor",
        paths["source"],
        "-o",
        paths["cleaned"],
    ]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    assert (
        result1.returncode == 0
    ), f"Script 1 (excel_guid_processor) failed: {result1.stderr}"
    assert os.path.exists(
        paths["cleaned"]
    ), "Cleaned Excel file was not created by the first script."

    # --- Step 2: Run the second script (Excel to SP file) ---
    cmd2 = [
        "python",
        "-m",
        "src.excel_to_shared_params",
        paths["cleaned"],
        "-o",
        paths["final_sp"],
        "--name-style",
        "pascal",
        "--suffix",
        "_Test",
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    assert (
        result2.returncode == 0
    ), f"Script 2 (excel_to_shared_params) failed: {result2.stderr}"
    assert os.path.exists(
        paths["final_sp"]
    ), "Final Shared Parameter file was not created by the second script."

    # --- Step 3: Validate the final Shared Parameter file ---
    with open(paths["final_sp"], "r", encoding="utf-16-le") as f:
        content = f.read()

    # Basic structure checks
    assert "*GROUP\tID\tNAME" in content
    assert "GROUP\t210\tGeneral" in content  # Note: Group ID is random, this might need adjustment
    assert "GROUP\t211\tElectrical" in content
    assert "*PARAM\tGUID\tNAME\tDATATYPE" in content

    # Specific parameter validation
    # Check 1: Correct data type inference (Length)
    assert (
        "PARAM\t908c188b-228c-4f7e-b351-61959bf2de\tOverallDiameter_Test\tLENGTH"
        in content
    )
    # Check 2: Description truncation and name conversion ("3D")
    assert (
        "PARAM\t7dd8432d-246b-439c-8760-2a8a2ced3aa4\tLuminaireHousingShape3D_Test\tTEXT\t\t210\t1\tA very long description that will most definitely need to be truncated at a word break to fit within the 254 character limit that is imposed by the Revit shared…\t1\t0"
        in content
    )
    # Check 3: "Identical with name" with no example becomes empty description
    assert (
        "PARAM\ted2b084e-3ddc-49c9-9bcb-37ec9810ba4e\tSiliconFree_Test\tYESNO\t\t210\t1\t\t1\t0"
        in content
    )
    # Check 4: Correct data type inference (Area)
    assert (
        "PARAM\taf6eff8d-c4fa-491d-918c-2980aea623b3\tWindage_Test\tAREA" in content
    )
    # Check 5: "Identical with name" with an example uses the example
    assert (
        "PARAM\t0120cf83-8dbc-454b-8a7a-8882f2c95df\tLightSourceIncluded_Test\tYESNO\t\t211\t1\te.g. Yes\t1\t0"
        in content
    )
