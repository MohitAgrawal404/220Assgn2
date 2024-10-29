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
    capacity, compulsory, total = 0, 0, 0
    for line in lines:
        tokens = [x.strip() for x in line.split(',')]
        if "DCACHE_MISS_CAPACITY" in line:
            capacity = float(tokens[1])
        elif "DCACHE_MISS_COMPULSORY" in line:
            compulsory = float(tokens[1])
        elif "DCACHE_MISS" in line:
            total = float(tokens[1])
    conflict = total - (capacity + compulsory)
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
        # Create expanded benchmark labels that include configuration info
        expanded_benchmarks = []

        for config_key in descriptor_data["configurations"].keys():
            for benchmark in benchmarks_org:
                benchmark_name = benchmark.split("/")[0]  # Get the first part as the benchmark name
                exp_path = os.path.join(sim_path, benchmark, descriptor_data["experiment"], config_key)

                # Initialize miss values
                capacity, compulsory, conflict = 0, 0, 0
                with open(os.path.join(exp_path, csv_name)) as f:
                    lines = f.readlines()
                    # Parse the cache miss stats from the lines
                    capacity, compulsory, conflict = parse_cache_misses(lines)

                # Append benchmark name with configuration for the expanded axis labels
                expanded_benchmarks.append(f"{benchmark_name}-{config_key}")

                # Append miss data for each configuration per benchmark
                cache_miss_data["Capacity Miss"].append(capacity)
                cache_miss_data["Compulsory Miss"].append(compulsory)
                cache_miss_data["Conflict Miss"].append(conflict)

        # Debug output
        print(f"Total expanded benchmarks: {len(expanded_benchmarks)}")
        print(f"Total Capacity Miss entries: {len(cache_miss_data['Capacity Miss'])}")
        print(f"Total Compulsory Miss entries: {len(cache_miss_data['Compulsory Miss'])}")
        print(f"Total Conflict Miss entries: {len(cache_miss_data['Conflict Miss'])}")

        # Pass the expanded benchmark labels to plot_data
        plot_data(expanded_benchmarks, cache_miss_data, plot_title, output_file)

    except Exception as e:
        print(f"Error: {e}")



def plot_data(benchmarks, data, ylabel_name, fig_name, ylim=None):
    print(data)
    colors = ['#800000', '#4363d8', '#f58231']
    ind = np.arange(len(benchmarks))
    width = 0.5  # Adjusted width for stacked bars

    fig, ax = plt.subplots(figsize=(19, 4.4), dpi=80)

    # Plot stacked bars
    bottom = np.zeros(len(benchmarks))
    for idx, (key, values) in enumerate(data.items()):
        ax.bar(ind, values, width=width, color=colors[idx], edgecolor='black', label=key, bottom=bottom)
        bottom += np.array(values)

    ax.set_xlabel("Benchmarks")
    ax.set_ylabel(ylabel_name)
    ax.set_xticks(ind)
    ax.set_xticklabels(benchmarks, rotation=27, ha='right')
    ax.grid('x')

    if ylim is not None:
        ax.set_ylim(ylim)

    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    plt.savefig(fig_name, format="pdf", bbox_inches="tight")

if __name__ == "__main__":
    # Create a parser for command-line arguments
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)
    plot_metric(descriptor_data, args.simulation_path, 'memory.stat.0.csv', os.path.join(args.output_dir, "DCACHE_MISS_STACKED.pdf"), "DCACHE Miss Breakdown")
