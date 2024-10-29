import os
import json
import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rc('font', size=14)

def read_descriptor_from_json(descriptor_filename):
    # Read the descriptor data from a JSON file
    try:
        with open(descriptor_filename, 'r') as json_file:
            descriptor_data = json.load(json_file)
        return descriptor_data
    except FileNotFoundError:
        print(f"Error: File '{descriptor_filename}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{descriptor_filename}': {e}")
        return None

def parse_cache_misses(lines):
    capacity, compulsory, conflict = None, None, None
    for line in lines:
        tokens = [x.strip() for x in line.split(',')]
        if "DCACHE_MISS_CAPACITY_pct" in line:
            capacity = float(tokens[1])
        elif "DCACHE_MISS_COMPULSURY_pct" in line:
            compulsory = float(tokens[1])
        elif "DCACHE_MISS_CONFLICT_pct" in line:
            conflict = float(tokens[1])
    assert((capacity is not None) and (compulsory is not None) and (conflict is not None))
    return capacity, compulsory, conflict

def plot_metric(descriptor_data, sim_path, csv_name, output_file, plot_title):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    cache_miss_data = {
        "Capacity Miss": [],
        "Compulsory Miss": [],
        "Conflict Miss": []
    }

    try:
        # Create expanded data structures for grouped plotting
        expanded_benchmarks = benchmarks_org.copy()  # One entry per benchmark
        grouped_cache_miss_data = {
            "Capacity Miss": [],
            "Compulsory Miss": [],
            "Conflict Miss": []
        }

        # Iterate over each benchmark and configuration
        for benchmark in benchmarks_org:
            capacity_miss_group = []
            compulsory_miss_group = []
            conflict_miss_group = []

            for config_key in descriptor_data["configurations"].keys():
                benchmark_name = benchmark.split("/")[0]  # Get the first part as the benchmark name
                exp_path = os.path.join(sim_path, benchmark, descriptor_data["experiment"], config_key)

                # Parse the cache miss stats
                with open(os.path.join(exp_path, csv_name)) as f:
                    lines = f.readlines()
                    capacity, compulsory, conflict = parse_cache_misses(lines)

                # Collect miss data per configuration for the current benchmark
                capacity_miss_group.append(capacity)
                compulsory_miss_group.append(compulsory)
                conflict_miss_group.append(conflict)

            # Append miss data for the benchmark (grouped by config)
            grouped_cache_miss_data["Capacity Miss"].append(capacity_miss_group)
            grouped_cache_miss_data["Compulsory Miss"].append(compulsory_miss_group)
            grouped_cache_miss_data["Conflict Miss"].append(conflict_miss_group)

        # Debug output to verify data
        print(f"Benchmarks: {expanded_benchmarks}")
        print(f"Capacity Miss Grouped Data: {grouped_cache_miss_data['Capacity Miss']}")
        print(f"Compulsory Miss Grouped Data: {grouped_cache_miss_data['Compulsory Miss']}")
        print(f"Conflict Miss Grouped Data: {grouped_cache_miss_data['Conflict Miss']}")

        # Plot the grouped data
        plot_data(expanded_benchmarks, grouped_cache_miss_data, plot_title, output_file)

    except Exception as e:
        print(f"Error: {e}")

def plot_data(benchmarks, grouped_data, ylabel_name, fig_name, ylim=None):
    num_benchmarks = len(benchmarks)
    num_configs = len(grouped_data["Capacity Miss"][0])  # Assuming all benchmarks have same number of configs

    ind = np.arange(num_benchmarks)  # 23 benchmark groups
    width = 0.12  # Width of each bar (smaller to accommodate multiple configurations)

    # Initialize the figure and axis
    fig, ax = plt.subplots(figsize=(19, 6))
    
    # For each configuration, we plot a bar for each miss type, stacked
    for i in range(num_configs):
        capacity_miss = [group[i] for group in grouped_data["Capacity Miss"]]
        compulsory_miss = [group[i] for group in grouped_data["Compulsory Miss"]]
        conflict_miss = [group[i] for group in grouped_data["Conflict Miss"]]

        # Plot the stacked bars
        bottom = np.zeros(num_benchmarks)
        p1 = ax.bar(ind + i * width, capacity_miss, width, label=f'Capacity Miss - Config {i+1}', color='blue')
        p3 = ax.bar(ind + i * width, conflict_miss, width, bottom=capacity_miss, label=f'Conflict Miss - Config {i+1}', color='red')
        p2 = ax.bar(ind + i * width, compulsory_miss, width, bottom=np.array(capacity_miss) + np.array(conflict_miss), label=f'Compulsory Miss - Config {i+1}', color='green')

    # Customize the labels, title, etc.
    ax.set_ylabel(ylabel_name)
    ax.set_xlabel("Benchmarks")
    ax.set_title("DCache Miss Type Ratios (Stacked)")
    ax.set_xticks(ind + width * (num_configs / 2 - 0.5))  # Center the tick labels
    ax.set_xticklabels(benchmarks, rotation=90)

    custom_handles = [
            plt.Rectangle((0, 0), 1, 1, color='red', label='Capacity Miss'),
            plt.Rectangle((0, 0), 1, 1, color='green', label='Compulsory Miss'),
            plt.Rectangle((0, 0), 1, 1, color='blue', label='Conflict Miss')
        ]
        
    ax.legend(handles=custom_handles, loc='upper right', title="Cache Miss Types")

    fig.tight_layout()
    plt.savefig(fig_name, format="pdf", bbox_inches="tight")
    plt.show()

if __name__ == "__main__":
    # Create a parser for command-line arguments
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)
    plot_metric(descriptor_data, args.simulation_path, 'memory.stat.0.csv', os.path.join(args.output_dir, "DCACHE_MISS_STACKED_RATIO.pdf"), "DCACHE Miss Type Percent")
