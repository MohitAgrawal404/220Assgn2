import os
import json
import argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import csv
from matplotlib import cm

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

def extract_ipc_and_dcache_miss_ratio(lines):
    ipc = 0
    dcache_misses = 0
    dcache_accesses = 0
    
    for line in lines:
        if "Periodic IPC" in line:
            ipc = float(line.split(',')[1].strip())
        elif "DCACHE_MISSES" in line:
            dcache_misses = float(line.split(',')[1].strip())
        elif "DCACHE_ACCESSES" in line:
            dcache_accesses = float(line.split(',')[1].strip())
    
    dcache_miss_ratio = dcache_misses / dcache_accesses if dcache_accesses > 0 else 0
    return ipc, dcache_miss_ratio

def plot_metrics(descriptor_data, sim_path, output_dir, benchmarks_per_plot=8):
    benchmarks_org = descriptor_data["workloads_list"]
    benchmarks = []
    ipc = {}
    dcache_miss_ratios = {}

    # Initialize dicts to hold data for each configuration
    for config_key in descriptor_data["configurations"].keys():
        ipc[config_key] = []
        dcache_miss_ratios[config_key] = []
    
    # Iterate through configurations and benchmarks to extract stats
    for config_key in descriptor_data["configurations"].keys():
        avg_ipc = 0.0
        avg_dcache_miss_ratio = 0.0
        num_benchmarks = 0

        for benchmark in benchmarks_org:
            benchmark_name = benchmark.split("/")[0]
            exp_path = os.path.join(sim_path, benchmark, descriptor_data["experiment"], config_key)
            
            try:
                with open(os.path.join(exp_path, 'memory.stat.0.csv')) as f:
                    lines = f.readlines()
                    ipc_value, dcache_miss_ratio = extract_ipc_and_dcache_miss_ratio(lines)
                    
                    avg_ipc += ipc_value
                    avg_dcache_miss_ratio += dcache_miss_ratio
                    ipc[config_key].append(ipc_value)
                    dcache_miss_ratios[config_key].append(dcache_miss_ratio)
                    
                    if benchmark_name not in benchmarks:
                        benchmarks.append(benchmark_name)
                    
                    num_benchmarks += 1
            except Exception as e:
                print(f"Error reading stats for {benchmark} in {config_key}: {e}")

        # Compute averages for this configuration
        ipc[config_key].append(avg_ipc / num_benchmarks if num_benchmarks > 0 else 0)
        dcache_miss_ratios[config_key].append(avg_dcache_miss_ratio / num_benchmarks if num_benchmarks > 0 else 0)
    
    benchmarks.append('Avg')

    # Plot data in groups of 8 benchmarks to avoid crowding
    num_plots = (len(benchmarks) - 1) // benchmarks_per_plot + 1
    for i in range(num_plots):
        start = i * benchmarks_per_plot
        end = min(start + benchmarks_per_plot, len(benchmarks) - 1)
        plot_group(benchmarks[start:end] + ['Avg'], ipc, "IPC", os.path.join(output_dir, f"IPC_plot_{i+1}.pdf"))
        plot_group(benchmarks[start:end] + ['Avg'], dcache_miss_ratios, "Dcache Miss Ratio", os.path.join(output_dir, f"Dcache_Miss_Ratio_plot_{i+1}.pdf"))

def plot_group(benchmarks, data, ylabel_name, fig_name, ylim=None):
    colors = ['#800000', '#911eb4', '#4363d8', '#f58231', '#3cb44b', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#e6beff', '#e6194b', '#000075', '#800000', '#9a6324', '#808080', '#ffffff', '#000000']
    ind = np.arange(len(benchmarks))
    width = 0.1  # Adjust width for multiple bars
    fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)
    num_keys = len(data.keys())

    idx = 0
    start_id = -int(num_keys / 2)
    for key in data.keys():
        hatch = '///' if idx % 2 == 0 else '\\\\'
        ax.bar(ind + (start_id + idx) * width, data[key], width=width, fill=False, hatch=hatch, color=colors[idx], edgecolor=colors[idx], label=key)
        idx += 1

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
    parser = argparse.ArgumentParser(description='Analyze simulation stats and plot results')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path for plots. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    # Read the descriptor file
    descriptor_data = read_descriptor_from_json(descriptor_filename)

    # Plot IPC and Dcache Miss Ratio metrics
    plot_metrics(descriptor_data, args.simulation_path, args.output_dir)
