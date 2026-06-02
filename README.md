# Heraklit Equivalence Checker

This tool checks whether one Heraklit run is a prefix of or equivalent to another. It can be used to verify that 
1. the steps used to model a system can properly model a system, and
2. next step predictions match the actual next steps, even under concurrency and non-determinism

## Usage

The tool requires step definitions in the format described below, and two runs to compare. It will then check whether the second run is a prefix of the first.

```
uv run checker.py --step-defs <step_definitions_file> --reference-run <reference_run_file> --checked-run <checked_run_file>
```

## Step Definition Format

The step definitions are provided in a JSON file. See `tests/step_defs/` for example files.

## Displaying the extracted run graphs

Run with `--display`, after doing `uv add graphviz` to install the graph visualization library. This can help understand how the tool combines the runs.

## Tests

To run the tests, use `uv run tester.py`. To pause on a failing test and display the graphs, use `uv run tester.py --display-failed`. The tests are located in the `tests/` directory. Each test consists of a step definition file in the first line, the expected result in the second line and the two runs (reference and checked) in the two following lines. 

The expected result can be `match`, `no match` or `error`. The first two indicate whether the second run is a prefix of the first, while `error` indicates that the tool should raise an error, for example due to invalid step definitions.

## Use as a library

The functionality is contained in the `checker.py` file, which can be imported and used in other Python code. The main function to use is `check_equivalence_step_file`, which takes the two runs and the path to the step definitions file as an argument and returns whether the first run is a prefix of the second.

