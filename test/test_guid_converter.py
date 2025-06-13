import pytest
from src.guid_converter import process_and_convert_guid

@pytest.mark.parametrize(
    "test_id, input_guid, expected_short, expected_long",
    [
        (
            "artifact_hyphen",  # Test ID for clear reporting in pytest
            "0nXXpyMbD4Qg- zHiMoFE$Kf",
            "0nXXpyMbD4QgzHiMoFE$Kf",
            "{31861cfc-5a53-446a-af51-b16c8f3bf529}"
        ),
        (
            "hyphen_and_newline",
            "0Wy67y94v1fhgh-\nSU3mbcgU",
            "0Wy67y94v1fhghSU3mbcgU",
            "{20f061fc-244e-41a6-baab-71e0f0966a9e}"
        ),
        (
            "multiple_artifacts",
            "3$hGY- wTMb2sQ53dzP$G- jc9\n",
            "3$hGYwTMb2sQ53dzP$Gjc9",
            "{ffad08ba-7569-42d9-a143-9fd67f42d989}"
        ),
        (
            "clean_input",
            "38wYgCHqr1A8vcapxWfUmV",
            "38wYgCHqr1A8vcapxWfUmV",
            "{c8ea2a8c-474d-4128-8e66-933ee0a5ec1f}"
        ),
         (
            "whitespace_and_underscore",
            " 19Z9XKYDT4p8HR0ZbD$wO_ ", # Leading/trailing space
            "19Z9XKYDT4p8HR0ZbD$wO_",
            "{498c9854-88d7-44cc-845b-02394dffa63e}"
        )
    ]
)
def test_successful_conversions(test_id, input_guid, expected_short, expected_long):
    """
    Tests various successful conversion scenarios using parametrization.
    The test_id is not used in the function but provides clarity in test reports.
    """
    short_guid, long_guid = process_and_convert_guid(input_guid)
    assert short_guid == expected_short
    assert long_guid == expected_long

@pytest.mark.parametrize(
    "test_id, corrupt_input",
    [
        ("too_short", "2o82$3_1A1"),
        ("too_long", "2o82$3_1A1-$AvGqgNePPgEXTRA"),
        ("invalid_chars", "not_a_valid_base64_guid!"),
        ("empty_string", ""),
        ("whitespace_only", "  \n\t "),
        ("none_input", None)
    ]
)
def test_invalid_and_corrupt_data(test_id, corrupt_input):
    """Tests that corrupt or invalid inputs fail gracefully."""
    short_guid, long_guid = process_and_convert_guid(corrupt_input)
    assert short_guid is None
    assert long_guid is None
