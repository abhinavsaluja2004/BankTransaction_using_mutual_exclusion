# Directory for test cases
$TEST_DIR = "tests"
# Directory for results
$RESULTS_DIR = "results"

# Create results directory if it doesn't exist
if (!(Test-Path -Path $RESULTS_DIR)) {
    New-Item -ItemType Directory -Path $RESULTS_DIR
}

# Function to run tests for a single test case
function Run-Test {
    param (
        [string]$testCase
    )
    
    $testPath = Join-Path -Path $TEST_DIR -ChildPath $testCase
    $resultPath = Join-Path -Path $RESULTS_DIR -ChildPath $testCase
    
    Write-Host "Running test case: $testCase"
    if (!(Test-Path -Path $resultPath)) {
        New-Item -ItemType Directory -Path $resultPath
    }
    
    # Run original algorithm
    Write-Host "  Running original algorithm..."
    go run main_og.go $testPath "original"
    Move-Item -Path "metrics_original.json" -Destination $resultPath -Force
    
    # Run optimized algorithm
    Write-Host "  Running optimized algorithm..."
    go run main_updated.go $testPath "optimized"
    Move-Item -Path "metrics_optimized.json" -Destination $resultPath -Force
    
    # Generate visualizations
    Write-Host "  Generating visualizations..."
    python visualize_metrics.py $resultPath $resultPath
    
    Write-Host "Test case $testCase completed. Results in $resultPath"
    Write-Host "----------------------------------------"
}

# If a specific test case is provided, run only that one
if ($args.Count -eq 1) {
    Run-Test -testCase $args[0]
} else {
    # Run all test cases found in the test directory
    $testCases = Get-ChildItem -Path $TEST_DIR -Directory
    foreach ($testCase in $testCases) {
        Run-Test -testCase $testCase.Name
    }
}

Write-Host "All tests completed."