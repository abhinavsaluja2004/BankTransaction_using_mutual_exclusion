import json
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def load_metrics(base_path):
    """
    Load metrics from JSON files for 'original' and 'optimized' algorithms.

    Args:
        base_path (str): The directory containing the metrics JSON files.

    Returns:
        list: A list of dictionaries, where each dictionary contains metrics
              for an algorithm, or an empty list if files are not found.
    """
    metrics = []

    # Try to load both original and optimized metrics
    algorithms = ['original', 'optimized']
    for alg in algorithms:
        file_path = os.path.join(base_path, f'metrics_{alg}.json')
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Add algorithm name to the data for easier plotting
                data['algorithm'] = alg.capitalize()
                metrics.append(data)
        except FileNotFoundError:
            print(f"Warning: Could not find metrics for {alg} algorithm at {file_path}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {file_path}. File might be empty or corrupted.")
        except Exception as e:
            print(f"An unexpected error occurred while loading {file_path}: {e}")

    # Ensure metrics are in a consistent order (original then optimized) if both exist
    if len(metrics) == 2:
        metrics.sort(key=lambda x: x['algorithm'], reverse=True) # 'Original' comes before 'Optimized'

    return metrics

def plot_bar_chart(ax, labels, values, title, ylabel, colors, value_format='{:.0f}', show_improvement=False, improvement_text="improvement"):
    """Helper function to create a bar chart."""
    bars = ax.bar(labels, values, color=colors)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', linestyle='--', alpha=0.7) # Add grid lines

    # Add value labels on bars
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., yval, value_format.format(yval), va='bottom', ha='center') # Position text slightly above bar

    # Add improvement percentage annotation
    if show_improvement and len(values) >= 2 and values[0] > 0:
        if improvement_text == "improvement" or improvement_text == "more efficient":
             improvement = ((values[0] - values[1]) / values[0]) * 100
             annotation_text = f'{improvement:.1f}% {improvement_text}'
        elif improvement_text == "faster":
            improvement = ((values[0] - values[1]) / values[0]) * 100
            annotation_text = f'{improvement:.1f}% {improvement_text}'
        else: # Default case or other types of comparison
             improvement = ((values[1] - values[0]) / values[0]) * 100 # Percentage change from original to optimized
             annotation_text = f'{improvement:.1f}% change'


        # Adjust annotation position based on max value
        y_pos = max(values) * 0.8 if max(values) > 0 else 1 # Avoid division by zero or negative values

        ax.annotate(annotation_text,
                    xy=(0.5, y_pos), # Position in the middle of the x-axis
                    xycoords='data',
                    xytext=(0, 20),  # Offset text slightly above
                    textcoords='offset points',
                    ha='center',
                    bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.9), # More prominent bbox
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2")) # Add an arrow

def create_message_comparison(ax, metrics):
    """Create bar chart comparing total messages."""
    labels = [m['algorithm'] for m in metrics]
    values = [m['totalMessages'] for m in metrics]
    colors = ['#3498db', '#2ecc71'] # Blue for Original, Green for Optimized

    plot_bar_chart(ax, labels, values, 'Total Message Count Comparison', 'Number of Messages', colors, show_improvement=True, improvement_text="reduction")

def create_duration_comparison(ax, metrics):
    """Create bar chart comparing execution duration."""
    labels = [m['algorithm'] for m in metrics]
    values = [m['durationMs'] for m in metrics]
    colors = ['#3498db', '#2ecc71'] # Blue for Original, Green for Optimized

    plot_bar_chart(ax, labels, values, 'Execution Duration Comparison', 'Duration (ms)', colors, value_format='{:.2f}', show_improvement=True, improvement_text="faster")

def create_message_breakdown(ax, metrics):
    """Create stacked bar chart showing request vs. approval messages."""
    labels = [m['algorithm'] for m in metrics]
    requests = [m['requests'] for m in metrics]
    approvals = [m['approvals'] for m in metrics]

    width = 0.35
    bar_request = ax.bar(labels, requests, width, label='Request Messages', color='#3498db') # Blue
    bar_approval = ax.bar(labels, approvals, width, bottom=requests, label='Approval Messages', color='#e74c3c') # Red

    ax.set_title('Message Type Breakdown')
    ax.set_ylabel('Number of Messages')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels to stacked bars
    for i in range(len(labels)):
        ax.text(i, requests[i] / 2, str(requests[i]), ha='center', va='center', color='white', fontweight='bold')
        ax.text(i, requests[i] + approvals[i] / 2, str(approvals[i]), ha='center', va='center', color='white', fontweight='bold')
        ax.text(i, requests[i] + approvals[i] + 10, str(requests[i] + approvals[i]), ha='center', va='bottom', color='black') # Total on top

def create_efficiency_chart(ax, metrics):
    """Create chart showing messages per transaction."""
    labels = [m['algorithm'] for m in metrics]
    values = [m['totalMessages'] / m['transactions'] if m.get('transactions', 0) > 0 else 0 for m in metrics] # Handle potential division by zero
    colors = ['#3498db', '#2ecc71'] # Blue for Original, Green for Optimized

    plot_bar_chart(ax, labels, values, 'Messages Per Transaction', 'Avg Messages/Transaction', colors, value_format='{:.2f}', show_improvement=True, improvement_text="more efficient")


def create_visualizations(metrics, output_dir):
    """Create performance visualizations from metrics data."""
    if not metrics or len(metrics) < 2:
        print("Error: Need metrics for at least two algorithms (original and optimized) to compare.")
        return

    # Set up figure layout for combined plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Mutual Exclusion Algorithm Performance Comparison', fontsize=16, y=1.02) # Adjust y for title position

    # Flatten axes array for easy iteration
    axes = axes.flatten()

    # Create subplots for different metrics
    create_message_comparison(axes[0], metrics)
    create_duration_comparison(axes[1], metrics)
    create_message_breakdown(axes[2], metrics)
    create_efficiency_chart(axes[3], metrics)

    # Save the combined figure
    plt.tight_layout(rect=[0, 0, 1, 0.98])  # Adjust for suptitle
    output_path_combined = os.path.join(output_dir, 'performance_comparison_combined.png')
    plt.savefig(output_path_combined)
    plt.close(fig) # Close the figure to free memory

    print(f"Combined visualization saved to {output_path_combined}")

    # Create additional single charts for better visibility if needed (optional, but good for presentations)
    create_single_charts(metrics, output_dir)

def create_single_charts(metrics, output_dir):
    """Create individual charts for better visibility."""
    if not metrics or len(metrics) < 2:
        return # Skip if not enough data

    # Message count comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    create_message_comparison(ax, metrics)
    output_path_msg = os.path.join(output_dir, 'message_comparison.png')
    plt.savefig(output_path_msg)
    plt.close(fig)
    print(f"Single chart saved to {output_path_msg}")

    # Duration comparison
    fig, ax = plt.subplots(figsize=(8, 6))
    create_duration_comparison(ax, metrics)
    output_path_duration = os.path.join(output_dir, 'duration_comparison.png')
    plt.savefig(output_path_duration)
    plt.close(fig)
    print(f"Single chart saved to {output_path_duration}")

    # Message type breakdown
    fig, ax = plt.subplots(figsize=(8, 6))
    create_message_breakdown(ax, metrics)
    output_path_breakdown = os.path.join(output_dir, 'message_breakdown.png')
    plt.savefig(output_path_breakdown)
    plt.close(fig)
    print(f"Single chart saved to {output_path_breakdown}")

    # Messages per transaction
    fig, ax = plt.subplots(figsize=(8, 6))
    create_efficiency_chart(ax, metrics)
    output_path_efficiency = os.path.join(output_dir, 'efficiency_chart.png')
    plt.savefig(output_path_efficiency)
    plt.close(fig)
    print(f"Single chart saved to {output_path_efficiency}")


def main():
    """Main function to load data and create visualizations."""
    if len(sys.argv) < 2:
        print("Usage: python visualize_metrics.py <metrics_directory> [output_directory]")
        return

    metrics_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else metrics_dir

    # Ensure output directory exists
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory {output_dir}: {e}")
        return

    # Load metrics from JSON files
    metrics = load_metrics(metrics_dir)

    # Create visualizations
    create_visualizations(metrics, output_dir)

if __name__ == "__main__":
    main()
