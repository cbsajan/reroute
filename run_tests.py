"""
Simple test runner for REROUTE - No pytest required.

Usage:
    python run_tests.py
    python run_tests.py --verbose
    python run_tests.py --test websocket
    python run_tests.py --test openapi_parser
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests(test_name=None, verbose=False):
    """Run tests without pytest.

    Args:
        test_name: Specific test to run (e.g., 'websocket', 'openapi_parser')
        verbose: Show detailed output
    """
    loader = unittest.TestLoader()

    if test_name:
        # Run specific test file
        test_module = f"tests.test_{test_name}"
        try:
            suite = loader.loadTestsFromName(test_module)
        except ImportError as e:
            print(f"Error: Could not find test '{test_name}'")
            print(f"Available tests:")
            print("  - websocket")
            print("  - openapi_parser")
            print("  - openapi_generator")
            print(f"\n{e}")
            return False
    else:
        # Discover all tests
        start_dir = project_root / "tests"
        suite = loader.discover(start_dir, pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


def main():
    """Main entry point."""
    args = sys.argv[1:]

    verbose = "--verbose" in args or "-v" in args

    # Get test name
    test_name = None
    for arg in args:
        if arg.startswith("--test="):
            test_name = arg.split("=")[1]
            break
        elif arg.startswith("-t="):
            test_name = arg.split("=")[1]
            break
        elif not arg.startswith("-"):
            test_name = arg
            break

    success = run_tests(test_name, verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
