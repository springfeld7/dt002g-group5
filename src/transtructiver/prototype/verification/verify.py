"""
SIV Verification Case: Variable Renaming

This script validates the SIVerifier's ability to handle identifier renaming.
It compares an original function CST against a mutated version where the 
function name and parameters have been obfuscated, using a coordinate-based 
manifest to maintain logical parity.

Transformation:
    - add(a, b) -> x_add(x_a, x_b)
    - return a + b -> return x_a + x_b
"""

import os
from src.transtructiver.prototype.mock.mock_cst import cst as original_cst
from src.transtructiver.prototype.mock.mock_mutated_cst import cst as mutated_cst
from src.transtructiver.prototype.verification.verifier import SIVerifier


mock_manifest = {
    "renamed_paths": {
        "0.0": "x_add",  # function_definition -> identifier (add)
        "0.1.0": "x_a",  # function_definition -> parameters -> identifier (a)
        "0.1.1": "x_b",  # function_definition -> parameters -> identifier (b)
        "0.2.0.0.0": "x_a",  # body -> return_stmt -> bin_expr -> identifier (a)
        "0.2.0.0.2": "x_b",  # body -> return_stmt -> bin_expr -> identifier (b)
    },
    "ignored_paths": [],
}


def main():
    """
    Executes a Parallel Recursive Walk to verify structural isomorphism
    specifically for identifier renaming mutations.
    """
    verifier = SIVerifier()

    print("--- TranStructIVer SIV Standalone Test ---")
    print("Verifying structural isomorphism for variable renaming...")

    is_valid = verifier.verify(original_cst, mutated_cst, mock_manifest)

    status = "PASS" if is_valid else "FAIL"

    print(f"\n[SUMMARY]")
    print(f"Status: {status}")

    if not is_valid:
        print("Detailed Errors:")
        for error in verifier.errors:
            print(f" - {error}")
    else:
        print("Result: 1.0 (All structural nodes and renames verified)")

    verifier.write_summary("MOCK_ADD_01", is_valid)
    print(f"\nSummary logged to: {os.path.join(os.getcwd(), 'summary_log.csv')}")


if __name__ == "__main__":
    main()
