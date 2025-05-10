#!/bin/bash

# Directory for test cases
TEST_DIR="tests"
# Directory for results
RESULTS_DIR="results"

# Create results directory if it doesn't exist
mkdir -p $RESULTS_DIR

# Function to run tests for a single test case
run_test() {
    local test_case=$1
    local test_path="$TEST_DIR/$test_case"
    local result_path="$RESULTS_DIR/$test_case"
    
    echo "Running test case: $test_case"
    mkdir -p "$result_path"
    
    # Run original algorithm
    echo "  Running original algorithm..."
    go run main.go "$test_path" "original"
    mv metrics_original.json "$result_path/"
    
    # Run optimized algorithm
    echo "  Running optimized algorithm..."
    go run main3.go "$test_path" "optimized"
    mv metrics_optimized.json "$result_path/"
    
    # Generate visualizations
    echo "  Generating visualizations..."
    python visualize_metrics.py "$result_path" "$result_path"
    
    echo "Test case $test_case completed. Results in $result_path"
    echo "----------------------------------------"
}

# If a specific test case is provided, run only that one
if [ $# -eq 1 ]; then
    run_test "$1"
else
    # Run all test cases found in the test directory
    for test_case in $(ls $TEST_DIR); do
        # Check if it's a directory
        if [ -d "$TEST_DIR/$test_case" ]; then
            run_test "$test_case"
        fi
    done
fi

echo "All tests completed."