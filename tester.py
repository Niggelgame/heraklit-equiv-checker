from checker import check_equivalence_step_file
import os


def get_test_files(directory):
    files = os.listdir(directory)
    return [os.path.join(directory, f) for f in files if f.endswith(".test") and os.path.isfile(os.path.join(directory, f))]

def parse_test_file(file, tests_dir):
    with open(file, "r", encoding="utf-8") as f:
        step_def_file = f.readline().strip()
        step_def_file = os.path.join(tests_dir, step_def_file)
        expected_match = f.readline().strip()
        run_ref = map(lambda a: a.strip(), f.readline().strip().split(","))
        run_check = map(lambda a: a.strip(), f.readline().strip().split(","))
    return step_def_file, expected_match, run_ref, run_check


GREEN_TEXT = "\033[92m"
RED_TEXT = "\033[91m"
ORANGE_TEXT = "\033[93m"
LIGHT_GRAY_TEXT = "\033[90m"
RESET_TEXT = "\033[0m"


if __name__ == "__main__":
    import argparse

    # flag whether to display and pause the graphs on failure
    argparse = argparse.ArgumentParser(description="Run equivalence tests for Heraklit runs")
    argparse.add_argument("--display-failed", action="store_true", help="Display the graphs of the runs and pause after failed test")
    argparse.add_argument("--run-only", help="Only run the test specified")


    args = argparse.parse_args()

    TESTS_DIR = "tests"

    test_files = get_test_files(TESTS_DIR)
    print("Test files found:")
    for f in test_files:
        print(f)
    
    if not args.run_only is None:
        test_files = filter(lambda a: args.run_only in a, test_files)
    
    print(f"\nRunning tests...")

    stats_total = 0
    stats_passed = 0
    stats_failed = 0
    stats_skipped = 0

    for test_file in test_files:
        print(f"\nTesting {test_file}...{LIGHT_GRAY_TEXT}")
        stats_total += 1
        try:
            step_def_file, expected_match, run_ref, run_check = parse_test_file(test_file, TESTS_DIR)
        except Exception as e:
            print(f"{ORANGE_TEXT}Error parsing test file {test_file}: {e}{RESET_TEXT}")
            stats_skipped += 1
            continue
        
        try:
            result = check_equivalence_step_file(run_ref, run_check, step_def_file, display=args.display_failed)
        except Exception as e:
            if expected_match == "error":
                print(f"{GREEN_TEXT}Test passed: Expected error occurred: {e}{RESET_TEXT}")
                stats_passed += 1
            else:
                print(f"{RED_TEXT}Test failed: Unexpected error occurred: {e}{RESET_TEXT}")
                stats_failed += 1
            continue
        if (result and expected_match == "match") or (not result and expected_match == "no match"):
            print(f"{GREEN_TEXT}Test passed{RESET_TEXT}")
            stats_passed += 1
        else:
            print(f"{RED_TEXT}Test failed{RESET_TEXT}")
            if args.display_failed:
                print(f"{LIGHT_GRAY_TEXT}Displaying graphs for failed test...{RESET_TEXT}")
                input("Press Enter to continue...")
            stats_failed += 1

    print(f"\nTest results:")
    

    print(f"Total tests: {stats_total}")
    print(f"{GREEN_TEXT}Passed: {stats_passed}{RESET_TEXT}")
    print(f"{RED_TEXT}Failed: {stats_failed}{RESET_TEXT}")
    print(f"{ORANGE_TEXT}Skipped: {stats_skipped}{RESET_TEXT}")