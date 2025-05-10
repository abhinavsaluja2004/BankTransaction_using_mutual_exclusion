import json
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def load_metrics_across_test_cases(base_results_path):
    """
    Load metrics_optimized.json from each subdirectory (test case) within the base results path.

    Args:
        base_results_path (str): The main directory containing subdirectories for each test case.

    Returns:
        list: A list of dictionaries, where each dictionary contains metrics
              for a specific test case, or an empty list if no metrics are found.
    """
    all_metrics = []
    # Iterate through all items in the base results directory
    try:
        items = os.listdir(base_results_path)
    except FileNotFoundError:
        print(f"Error: Base results directory not found at {base_results_path}")
        return []
    except Exception as e:
        print(f"An error occurred while listing directory {base_results_path}: {e}")
        return []


    for item_name in items:
        item_path = os.path.join(base_results_path, item_name)

        # Check if the item is a directory (representing a test case)
        if os.path.isdir(item_path):
            test_case_name = item_name
            metrics_file_path = os.path.join(item_path, 'metrics_optimized.json')

            # Check if the optimized metrics file exists in the test case directory
            if os.path.exists(metrics_file_path):
                try:
                    with open(metrics_file_path, 'r') as f:
                        data = json.load(f)
                        # Add test case name to the data
                        data['testCase'] = test_case_name
                        all_metrics.append(data)
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON from {metrics_file_path}. File might be empty or corrupted.")
                except Exception as e:
                    print(f"An unexpected error occurred while loading {metrics_file_path}: {e}")
            else:
                print(f"Warning: Metrics file 'metrics_optimized.json' not found for test case '{test_case_name}' at {metrics_file_path}")

    # Sort metrics by test case name for consistent plotting order
    all_metrics.sort(key=lambda x: x['testCase'])

    return all_metrics

def plot_bar_chart(ax, labels, values, title, ylabel, colors):
    """Helper function to create a bar chart."""
    bars = ax.bar(labels, values, color=colors)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', linestyle='--', alpha=0.7) # Add grid lines

    # Add value labels on bars
    for bar in bars:
        yval = bar.get_height()
        # Use appropriate format based on the metric
        if 'Duration' in title:
             ax.text(bar.get_x() + bar.get_width()/2., yval, f'{yval:.2f}', va='bottom', ha='center')
        elif 'Messages Per Transaction' in title:
             ax.text(bar.get_x() + bar.get_width()/2., yval, f'{yval:.2f}', va='bottom', ha='center')
        else: # Assuming integer counts for messages (including Accounts and Transactions)
             ax.text(bar.get_x() + bar.get_width()/2., yval, f'{int(yval)}', va='bottom', ha='center')


    # Rotate x-axis labels for better fitting
    # Always rotate if there's more than one bar, and adjust rotation angle
    if len(labels) > 0:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9) # Increased rotation, smaller font, right alignment


def create_message_comparison(ax, metrics):
    """Create bar chart comparing total messages across test cases with accounts/transactions in labels."""
    # Format labels to include accounts and transactions
    labels = [f"{m['testCase']} (acc: {m['accounts']}, tran: {m['transactions']})" for m in metrics]
    values = [m['totalMessages'] for m in metrics]
    # Use a single color or a color map since we are not comparing two algorithms
    colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))

    plot_bar_chart(ax, labels, values, 'Total Message Count Across Test Cases', 'Number of Messages', colors)

def create_duration_comparison(ax, metrics):
    """Create bar chart comparing execution duration across test cases with accounts/transactions in labels."""
    # Format labels to include accounts and transactions
    labels = [f"{m['testCase']} (acc: {m['accounts']}, tran: {m['transactions']})" for m in metrics]
    values = [m['durationMs'] for m in metrics]
    colors = plt.cm.plasma(np.linspace(0, 1, len(labels))) # Use a different color map

    plot_bar_chart(ax, labels, values, 'Execution Duration Across Test Cases', 'Duration (ms)', colors)

def create_message_breakdown(ax, metrics):
    """Create stacked bar chart showing request vs. approval messages across test cases with accounts/transactions in labels."""
    # Format labels to include accounts and transactions
    labels = [f"{m['testCase']} (acc: {m['accounts']}, tran: {m['transactions']})" for m in metrics]
    requests = [m['requests'] for m in metrics]
    approvals = [m['approvals'] for m in metrics]

    width = 0.6 # Make bars slightly wider for single algorithm
    # Use different shades or patterns for request/approval within each test case color
    # Generate base colors from a colormap
    base_colors = plt.cm.viridis(np.linspace(0, 1, len(labels)))
    # Create slightly darker and lighter shades for stacking
    colors_req = base_colors * 0.8
    colors_app = np.minimum(base_colors * 1.2, 1.0) # Clamp values to 1.0

    x = np.arange(len(labels)) # the label locations

    bar_request = ax.bar(x, requests, width, label='Request Messages', color=colors_req)
    bar_approval = ax.bar(x, approvals, width, bottom=requests, label='Approval Messages', color=colors_app)

    ax.set_title('Message Type Breakdown Across Test Cases')
    ax.set_ylabel('Number of Messages')
    ax.set_xticks(x)
    ax.set_xticklabels(labels) # Use the formatted labels
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels to stacked bars
    for i in range(len(labels)):
        total = requests[i] + approvals[i]
        # Only add labels if values are significant enough to be visible
        if requests[i] > (total * 0.05): # Add threshold
             ax.text(i, requests[i] / 2, f'{int(requests[i])}', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
        if approvals[i] > (total * 0.05): # Add threshold
             ax.text(i, requests[i] + approvals[i] / 2, f'{int(approvals[i])}', ha='center', va='center', color='white', fontweight='bold', fontsize=8)
        if total > 0: # Only show total if there are messages
            ax.text(i, total + max(requests + approvals) * 0.02, f'{int(total)}', ha='center', va='bottom', color='black', fontsize=9) # Total on top

    # Rotate x-axis labels for better fitting
    if len(labels) > 0:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9) # Increased rotation, smaller font, right alignment


def create_efficiency_chart(ax, metrics):
    """Create chart showing messages per transaction across test cases with accounts/transactions in labels."""
    # Format labels to include accounts and transactions
    labels = [f"{m['testCase']} (acc: {m['accounts']}, tran: {m['transactions']})" for m in metrics]
    values = [m['totalMessages'] / m['transactions'] if m.get('transactions', 0) > 0 else 0 for m in metrics] # Handle potential division by zero
    colors = plt.cm.cividis(np.linspace(0, 1, len(labels))) # Use another color map

    plot_bar_chart(ax, labels, values, 'Messages Per Transaction Across Test Cases', 'Avg Messages/Transaction', colors)

    # Rotate x-axis labels for better fitting
    if len(labels) > 0:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9) # Increased rotation, smaller font, right alignment


def create_visualizations(metrics, output_dir):
    """Create performance visualizations from metrics data."""
    if not metrics:
        print("Error: No metrics data found for visualization.")
        return

    # Set up figure layout for combined plot (2 rows, 2 columns)
    # Increased figure width to give more space for labels
    fig, axes = plt.subplots(2, 2, figsize=(18, 10)) # Increased figure width
    fig.suptitle('Optimized Algorithm Performance Across Test Cases', fontsize=16, y=1.02) # Adjust y for title position

    # Flatten axes array for easy iteration
    axes = axes.flatten()

    # Create subplots for different metrics
    create_message_comparison(axes[0], metrics)
    create_duration_comparison(axes[1], metrics)
    create_message_breakdown(axes[2], metrics)
    create_efficiency_chart(axes[3], metrics)


    # Save the combined figure
    plt.tight_layout(rect=[0, 0, 1, 0.98])  # Adjust for suptitle
    output_path_combined = os.path.join(output_dir, 'optimized_performance_comparison_combined.png')
    plt.savefig(output_path_combined)
    plt.close(fig) # Close the figure to free memory

    print(f"Combined visualization saved to {output_path_combined}")

    # Create additional single charts for better visibility (optional)
    create_single_charts(metrics, output_dir)

def create_single_charts(metrics, output_dir):
    """Create individual charts for better visibility."""
    if not metrics:
        return # Skip if no data

    # Message count comparison
    fig, ax = plt.subplots(figsize=(12, 6)) # Increased width for single charts
    create_message_comparison(ax, metrics)
    output_path_msg = os.path.join(output_dir, 'optimized_message_comparison.png')
    plt.savefig(output_path_msg)
    plt.close(fig)
    print(f"Single chart saved to {output_path_msg}")

    # Duration comparison
    fig, ax = plt.subplots(figsize=(12, 6)) # Increased width for single charts
    create_duration_comparison(ax, metrics)
    output_path_duration = os.path.join(output_dir, 'optimized_duration_comparison.png')
    plt.savefig(output_path_duration)
    plt.close(fig)
    print(f"Single chart saved to {output_path_duration}")

    # Message type breakdown
    fig, ax = plt.subplots(figsize=(12, 6)) # Increased width for single charts
    create_message_breakdown(ax, metrics)
    output_path_breakdown = os.path.join(output_dir, 'optimized_message_breakdown.png')
    plt.savefig(output_path_breakdown)
    plt.close(fig)
    print(f"Single chart saved to {output_path_breakdown}")

    # Messages per transaction
    fig, ax = plt.subplots(figsize=(12, 6)) # Increased width for single charts
    create_efficiency_chart(ax, metrics)
    output_path_efficiency = os.path.join(output_dir, 'optimized_efficiency_chart.png')
    plt.savefig(output_path_efficiency)
    plt.close(fig)
    print(f"Single chart saved to {output_path_efficiency}")


def main():
    """Main function to load data and create visualizations."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_metrics_workloads.py <base_results_directory> [output_directory]")
        print("The base_results_directory should contain subdirectories for each test case,")
        print("each containing a 'metrics_optimized.json' file.")
        return

    metrics_base_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else metrics_base_dir

    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory {output_dir}: {e}")
        return

    # Load metrics from JSON files across test case directories
    metrics = load_metrics_across_test_cases(metrics_base_dir)

    # Create visualizations
    create_visualizations(metrics, output_dir)

if __name__ == "__main__":
    main()
