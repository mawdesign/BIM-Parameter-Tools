import pytest
from guid_converter import process_and_convert_guid

@pytest.mark.parametrize(
    "test_id, input_guid, expected_short, expected_long",
    [
        (
            "artifact_hyphen",  # Test ID for clear reporting in pytest
            "OjUoLaQbSJa-\nLY55KONd1nQ",
            "OjUoLaQbSJaLY55KONd1nQ",
            "3a35282d-a41b-4896-8b63-9e4a38d7759d"
        ),
        (
            "artifact_underscore",
            # This tests that an underscore at a break is removed,
            # but another legitimate hyphen is preserved.
            "cixB5W58tU-_\naKxNn4u0Vg",
            "cixB5W58tU-aKxNn4u0Vg",
            "722c41e5-6e7c-b54f-be68-ac4d9f8bb456"
        ),
        (
            "legitimate_hyphen",
            # This tests the case where the hyphen at the break is part of the GUID.
            "qn5yQy-\nFpkqfWJtOCWqM8Q",
            "qn5yQy-FpkqfWJtOCWqM8Q",
            "aa7e7243-2f85-a64a-9f58-9b4e096a8cf1"
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

def test_corrupt_data_returns_none():
    """
    Tests that genuinely corrupt data fails gracefully and returns (None, None).
    """
    corrupt_input = "ThisIsJust-\nSomeJunkData"
    short_guid, long_guid = process_and_convert_guid(corrupt_input)
    assert short_guid is None
    assert long_guid is None

@pytest.mark.parametrize(
    "invalid_input",
    [
        "",  # Empty string
        "single_line_string_no_newline",  # No newline character
        None  # None value
    ]
)
def test_invalid_inputs_return_none(invalid_input):
    """
    Tests that the function handles edge cases like empty, single-line,
    or None inputs by returning (None, None) as per its contract.
    """
    # Note: The function expects a string, but we test None to be robust.
    # A static type checker would flag this, but it's a good runtime check.
    if invalid_input is None:
        with pytest.raises(AttributeError):
             process_and_convert_guid(invalid_input)
    else:
        short_guid, long_guid = process_and_convert_guid(invalid_input)
        assert short_guid is None
        assert long_guid is None
