# Location: File test_engine.py (Complete Replacement)

# This script is designed to test the core functionalities of our soul_engine.
# It does not create a product; it *proves* that our engine is reliable.

import pydantic
from soul_engine import SystemBlueprint
import json
import os  # <-- SURGICAL ADDITION #1
import pytest

# --- Intelligent Path Setup --- # <-- SURGICAL ADDITION #2 (Whole Block)
# This clever piece of code finds the directory where this script lives.
# This makes the script work no matter where you run it from.
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Now, we create an absolute path to our data file.
DATA_FILE_PATH = os.path.join(SCRIPT_DIRECTORY, "Labyrinth_Test_System.json")


# --- Helper function for clean output ---
def run_test(test_name: str, test_function):
    """A simple wrapper to make test output clear and readable."""
    print(f"--- Running Test: {test_name} ---")
    try:
        test_function()
        print(f"[ PASS ] {test_name}\n")
        return True
    except (pydantic.ValidationError, ValueError) as e:
        print(f"[ FAIL ] {test_name}")
        print("    Error Details:")
        # We indent the error to make it easy to read
        for line in str(e).split("\n"):
            print(f"      > {line}")
        print("")
        return False
    except FileNotFoundError as e:
        # Improved error message to show the full path it was looking for
        print(f"[ FAIL ] {test_name}")
        print(
            "    Error: File not found. The script was looking for a file at this location:"
        )
        print(f"      > {e.filename}")
        print("")
        return False


# --- Test Case 1: Loading a valid blueprint ---
def test_load_valid_file():
    """Checks if a known-good JSON file loads without errors."""
    # MODIFIED LINE: Uses the full path now
    blueprint = SystemBlueprint.from_file(DATA_FILE_PATH)
    # A simple check to ensure data was loaded correctly
    assert blueprint.project_details.name == "Labyrinth_Test_System"


# --- Test Case 2: Saving and re-loading ---
def test_save_and_reload():
    """Ensures we can save a blueprint and load it back without data loss."""
    # MODIFIED LINE: Uses the full path now
    original_blueprint = SystemBlueprint.from_file(DATA_FILE_PATH)

    # MODIFIED LINE: Ensures temp file is saved in the script's directory
    save_path = os.path.join(SCRIPT_DIRECTORY, "temp_test_output.json")
    original_blueprint.to_file(save_path)

    reloaded_blueprint = SystemBlueprint.from_file(save_path)

    # The most important check: Is the re-loaded data identical to the original?
    assert original_blueprint.model_dump() == reloaded_blueprint.model_dump()


# --- Test Case 3: Detecting an invalid node ID ---
def test_detects_bad_pipe_connection():
    """
    Checks if our smart validator catches a pipe that connects to a
    non-existent node by confirming it raises the correct error.
    """
    with open(DATA_FILE_PATH, "r") as f:
        data = json.load(f)

    # Intentionally introduce an error
    data["pipes"][0]["source_node"] = "this_node_does_not_exist"

    # This is the proper way to test for an expected error.
    # The test PASSES if a ValidationError occurs inside this block.
    with pytest.raises(pydantic.ValidationError) as e:
        SystemBlueprint(**data)

    # Optional: A more advanced check to ensure the error message is correct.
    assert "has an invalid source_node" in str(e.value)


# --- Test Case 4: Detecting a bad default profile ---
def test_detects_bad_profile_id():
    """
    Checks if our smart validator catches when the default profile ID
    is not defined in the profiles list.
    """
    # MODIFIED LINE: Uses the full path now
    with open(DATA_FILE_PATH, "r") as f:
        data = json.load(f)

    # Intentionally introduce an error
    data["system_tuning_parameters"]["default_profile_id"] = "unbalanced_and_flawed"

    # This line *should* raise a validation error
    SystemBlueprint(**data)


def test_detects_disconnected_component():
    """
    Checks if our graph validator catches a system that is physically
    split into two or more non-connected parts.
    """
    with open(DATA_FILE_PATH, "r") as f:
        data = json.load(f)

    # Intentionally add a new, disconnected island of components
    data["nodes"].append(
        {"node_id": "orphan_inlet", "type": "inlet", "label": "Orphan Inlet"}
    )
    data["nodes"].append(
        {"node_id": "orphan_outlet", "type": "outlet", "label": "Orphan Outlet"}
    )
    data["pipes"].append(
        {
            "pipe_id": "P_ORPHAN",
            "source_node": "orphan_inlet",
            "target_node": "orphan_outlet",
            "flow_sensor": {
                "sensor_id": "S_ORPHAN",
                "label": "Orphan",
                "gpio_pin": 99,
                "k_factor_ppl": 450.0,
            },
            "properties": {"length_m": 1.0, "inner_diameter_m": 0.010},
        }
    )

    # This should now raise a ValidationError because the graph is not connected
    with pytest.raises(pydantic.ValidationError) as e:
        SystemBlueprint(**data)

    # Check for the specific error message from our new validator
    assert "is not a single connected graph" in str(e.value)


# --- Main execution block ---
if __name__ == "__main__":
    print(">>> Starting Soul Engine Test Suite <<<\n")

    passed_tests = 0
    total_tests = 5  # <-- This is changed from 4 to 5

    # Fix the deprecation warning in the test_save_and_reload function first
    def fixed_test_save_and_reload():
        original_blueprint = SystemBlueprint.from_file(DATA_FILE_PATH)
        save_path = os.path.join(SCRIPT_DIRECTORY, "temp_test_output.json")
        original_blueprint.to_file(save_path)
        reloaded_blueprint = SystemBlueprint.from_file(save_path)
        assert original_blueprint.model_dump() == reloaded_blueprint.model_dump()

    # The test runner block
    if run_test("Load Valid File", test_load_valid_file):
        passed_tests += 1
    if run_test("Save and Reload", fixed_test_save_and_reload):
        passed_tests += 1
    if run_test("Detect Bad Pipe Connection", test_detects_bad_pipe_connection):
        passed_tests += 1
    if run_test("Detect Bad Profile ID", test_detects_bad_profile_id):
        passed_tests += 1
    if run_test("Detect Disconnected Component", test_detects_disconnected_component):
        passed_tests += 1  # <-- This is the new line

    print("--- Test Suite Complete ---")
    print(f"Result: {passed_tests} / {total_tests} tests passed.")
    print("---------------------------\n")

    if passed_tests == total_tests:
        print("✅ All engine tests passed successfully. The core engine is reliable!")
    else:
        print("❌ Some engine tests failed. Please review the errors above.")
