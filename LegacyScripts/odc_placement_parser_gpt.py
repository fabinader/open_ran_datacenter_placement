import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use the non-interactive Agg backend
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import locale
import contextily as ctx
from pyproj import Proj, Transformer
import multiprocessing
import time
import imageio
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from sklearn.cluster import KMeans
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultSingleObjectiveTermination
from functools import partial
import math
import argparse
import os
from sklearn.exceptions import ConvergenceWarning
import re
import warnings

# Set locale to ensure dot-separated decimal representation
locale.setlocale(locale.LC_NUMERIC, 'C')

frames = []

def haversine_np(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

# Function to extract bandwidth from ITU standard for radio emission designations
def extract_bandwidth(designation):
    unit_dict = {
        'H': 1e-6,    # Hertz to Megahertz
        'K': 1e-3,    # Kilohertz to Megahertz
        'M': 1,       # Megahertz to Megahertz
        'G': 1e3      # Gigahertz to Megahertz
    }
    
    for i, char in enumerate(designation):
        if char in unit_dict:
            numeric_part = designation[:i]
            unit = char
            break
    
    bandwidth_mhz = float(numeric_part) * unit_dict[unit]
    return bandwidth_mhz

# Function to calculate the number of CPU cores required based on bandwidth
def calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz):
    return (bandwidth_mhz / 100) * cpu_per_100mhz

# Reading O-RU client data
def read_clients(file_path, cpu_per_100mhz):
    df = pd.read_csv(file_path, converters={
        'latitude': locale.atof,
        'longitude': locale.atof
    })
    clients = []
    for index, row in df.iterrows():
        bandwidth_mhz = extract_bandwidth(row['emission_designation'])
        cpu_cores = calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz)
        client = {
            "cell_site_id": row['cell_site_id'],
            "emission_designation": row['emission_designation'],
            "technology": row['technology'],
            "tx_frequency": row['tx_frequency'],
            "rx_frequency": row['rx_frequency'],
            "azimuth": row['azimuth'],
            "antenna_gain": row['antenna_gain'],
            "back_front_relation": row['back_front_relation'],
            "hpa": row['hpa'],
            "mechanical_elevation": row['mechanical_elevation'],
            "polarization": row['polarization'],
            "antenna_height": row['antenna_height'],
            "tx_power": row['tx_power'],
            "latitude": row['latitude'],
            "longitude": row['longitude'],
            "cell_carrier_id": row['cell_carrier_id'],
            "bandwidth_mhz": bandwidth_mhz,
            "cpu_cores": math.ceil(cpu_cores),
            "oru_id": index + 1  # Assigning O-RU ID
        }
        clients.append(client)
    return clients

# Generate initial ODC locations using KMeans
def generate_initial_odcs(clients, num_initial_odcs):
    distinct_clusters = 0
    n_clusters = 0
    lat_lon = np.array([[c["latitude"], c["longitude"]] for c in clients])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        kmeans = KMeans(n_clusters=num_initial_odcs, random_state=0).fit(lat_lon)
        initial_odcs = kmeans.cluster_centers_
        # Check if a ConvergenceWarning was raised
        if w and issubclass(w[-1].category, ConvergenceWarning):
            warning_message = str(w[-1].message)
            print("ConvergenceWarning was raised")
            print(warning_message)
            
            # Extract numbers from the warning message using regex
            numbers = re.findall(r'\d+', warning_message)
            if len(numbers) >= 2:
                distinct_clusters = int(numbers[0])
                n_clusters = int(numbers[1])
                print(f"Number of distinct clusters: {distinct_clusters}")
                print(f"n_clusters: {n_clusters}")
                kmeans = KMeans(n_clusters=distinct_clusters, random_state=0).fit(lat_lon)
                initial_odcs = kmeans.cluster_centers_
                
            else:
                print("Could not extract the required numbers from the warning message.")
        else:
            print("No ConvergenceWarning")
    return [(lat, lon) for lat, lon in initial_odcs]

# Function to evaluate a single trial
def evaluate_trial(i, X, clients, initial_odcs, max_distance, max_capacity, distances):
    num_odcs = len(initial_odcs)
    selected_odcs = [initial_odcs[j] for j in range(num_odcs) if X[i, j] > 0.5]
    if len(selected_odcs) == 0:
        return (1, 1, 0, 0, float('inf'))  # Set constraints to invalid, return default values

    capacities = np.zeros(len(selected_odcs))
    distances_list = []  # To calculate average distance
    odc_indices = [k for k in range(num_odcs) if X[i, k] > 0.5]

    for client_idx, client in enumerate(clients):
        if selected_odcs:
            selected_distances = distances[client_idx, odc_indices]
            closest_odc_idx = np.argmin(selected_distances)
            closest_odc = selected_odcs[closest_odc_idx]
            capacities[closest_odc_idx] += client["cpu_cores"]
            distances_list.append(selected_distances[closest_odc_idx])

    valid = np.all(capacities <= max_capacity)
    constraint0 = 0 if valid else 1

    valid_distance = np.all(np.array(distances_list) <= max_distance)
    constraint1 = 0 if valid_distance else 1

    total_capacity = np.sum(capacities)
    num_active_odc = len(selected_odcs)
    avg_distance = np.mean(distances_list) if distances_list else float('inf')

    return (constraint0, constraint1, total_capacity, num_active_odc, avg_distance)

class ODCPlacementProblem(Problem):
    def __init__(self, clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_processes, distances, obj_weights):
        self.clients = clients
        self.initial_odcs = initial_odcs
        self.max_distance = max_distance
        self.max_capacity = max_capacity
        self.cpu_per_100mhz = cpu_per_100mhz
        self.no_processes = no_processes
        self.distances = distances
        self.obj_weights = obj_weights  # Adding obj_weights as a class attribute
        super().__init__(
            n_var=len(initial_odcs),
            n_obj=3,  # Three objectives
            n_constr=2,
            xl=0,
            xu=1
        )

    def _evaluate(self, X, out, *args, **kwargs):
        n_trials = X.shape[0]
        num_clients = len(self.clients)
        num_odcs = len(self.initial_odcs)

        total_capacities = np.zeros(n_trials)
        num_active_odcs = np.zeros(n_trials)
        avg_distances = np.zeros(n_trials)  # New objective for average distance
        constraints = np.zeros((n_trials, 2))

        # Use partial to pass fixed arguments
        evaluate_trial_partial = partial(evaluate_trial, X=X, clients=self.clients, initial_odcs=self.initial_odcs, max_distance=self.max_distance, max_capacity=self.max_capacity, distances=self.distances)

        # Use ProcessPoolExecutor to parallelize the evaluation
        with ProcessPoolExecutor(max_workers=self.no_processes) as executor:
            results = list(executor.map(evaluate_trial_partial, range(n_trials)))

        # Unpack the results
        for i, (constraint0, constraint1, total_capacity, num_active_odc, avg_distance) in enumerate(results):
            constraints[i, 0] = constraint0
            constraints[i, 1] = constraint1
            total_capacities[i] = total_capacity
            num_active_odcs[i] = num_active_odc
            avg_distances[i] = avg_distance

        # Normalize the objective values
        max_capacity_value = np.max(total_capacities)
        max_avg_distance_value = np.max(avg_distances)
        max_num_active_odcs = np.max(num_active_odcs)

        # Handle the case where the max values are zero to avoid division by zero
        max_capacity_value = max_capacity_value if max_capacity_value != 0 else 1
        max_avg_distance_value = max_avg_distance_value if max_avg_distance_value != 0 else 1
        max_num_active_odcs = max_num_active_odcs if max_num_active_odcs != 0 else 1

        f1 = total_capacities / max_capacity_value  # Normalize total capacity
        f2 = num_active_odcs / max_num_active_odcs  # Normalize number of active ODCs
        f3 = avg_distances / max_avg_distance_value  # Normalize average distance

        out["F"] = np.column_stack([self.obj_weights[0] * f1, self.obj_weights[1] * f2, self.obj_weights[2] * f3])  # Apply weights to objectives
        out["G"] = constraints

def optimize_placement(clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_generations, no_processes, distances, obj_weights):
    problem = ODCPlacementProblem(clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_processes, distances, obj_weights)
    algorithm = NSGA2(pop_size=100)
    termination = DefaultSingleObjectiveTermination(
    xtol=1e-8,  # The algorithm stops if the change in decision variables is less than "xtol" for a period of "period" generations
    cvtol=1e-8,  # The algortihm stops if the change in constraints violations is less than "cvtol" for a period of "period" generations
    ftol=1e-8,  # The algortihm stops if the change in objective functions values is less than "ftol" for a period of "period" generations
    period=60,  # Set the number os generations to evaluate xtol, cvtol and ftol
    n_max_gen=no_generations  # Set the maximum number of generations the algorithm will run
    )
    res = minimize(problem, algorithm, termination, seed=1, save_history=True, verbose=True)
    return res

def plot_results(res, initial_odcs, clients, trial, save_as_gif, output_directory):
    plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1])

    ax_map = plt.subplot(gs[:, 0])
    ax_obj = plt.subplot(gs[0, 1])
    ax_hist = plt.subplot(gs[1, 1])

    # Map plot
    latitudes = [client['latitude'] for client in clients]
    longitudes = [client['longitude'] for client in clients]
    ax_map.scatter(longitudes, latitudes, c='blue', label='Clients')

    # Extract selected ODCs
    selected_odcs = [initial_odcs[i] for i in range(len(initial_odcs)) if res.X[trial, i] > 0.5]
    odc_latitudes = [odc[0] for odc in selected_odcs]
    odc_longitudes = [odc[1] for odc in selected_odcs]
    ax_map.scatter(odc_longitudes, odc_latitudes, c='red', marker='x', label='Selected ODCs')

    ax_map.set_title('ODC Placement Map')
    ax_map.set_xlabel('Longitude')
    ax_map.set_ylabel('Latitude')
    ax_map.legend()
    ctx.add_basemap(ax_map, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron)

    # Objective values plot
    f1 = res.F[:, 0]
    f2 = res.F[:, 1]
    f3 = res.F[:, 2]
    ax_obj.plot(f1, label='Normalized Capacity')
    ax_obj.plot(f2, label='Normalized Number of ODCs')
    ax_obj.plot(f3, label='Normalized Avg Distance')
    ax_obj.set_title('Objective Values')
    ax_obj.legend()

    # Convergence history plot
    n_evals = np.arange(1, len(res.history) + 1)
    opt = [e.opt[0].F for e in res.history]
    ax_hist.plot(n_evals, opt)
    ax_hist.set_title('Convergence History')
    ax_hist.set_xlabel('Generation')
    ax_hist.set_ylabel('Objective Function Value')

    plt.tight_layout()
    output_file = os.path.join(output_directory, f'odc_placement_results_trial_{trial}.png')
    plt.savefig(output_file)  # Save the figure as PNG
    if save_as_gif:
        frames.append(imageio.v2.imread(output_file))  # Save the frame for GIF
    else:
        plt.close()

def main(clients_csv, num_initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_generations, no_processes, save_as_gif, output_directory, obj_weights):
    clients = read_clients(clients_csv, cpu_per_100mhz)
    initial_odcs = generate_initial_odcs(clients, num_initial_odcs)
    distances = np.zeros((len(clients), len(initial_odcs)))

    for i, client in enumerate(clients):
        for j, odc in enumerate(initial_odcs):
            distances[i, j] = haversine_np(client['latitude'], client['longitude'], odc[0], odc[1])

    res = optimize_placement(clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_generations, no_processes, distances, obj_weights)

    os.makedirs(output_directory, exist_ok=True)  # Ensure the output directory exists

    for trial in range(len(res.X)):
        plot_results(res, initial_odcs, clients, trial, save_as_gif, output_directory)
    
    if save_as_gif:
        gif_output_file = os.path.join(output_directory, 'odc_placement_results.gif')
        imageio.mimsave(gif_output_file, frames, fps=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Optimize ODC placement')
    parser.add_argument('--clients_csv', type=str, default="/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/CityData/Manaus.csv", help='Path to clients CSV file')
    parser.add_argument('--num_initial_odcs', type=int, default=100, help='Number of initial ODCs')
    parser.add_argument('--max_distance', type=float, default=11.0, help='Maximum distance (in km)')
    parser.add_argument('--max_capacity', type=float, default=1000.0, help='Maximum capacity')
    parser.add_argument('--cpu_per_100mhz', type=float, default=14.0, help='CPU cores per 100 MHz')
    parser.add_argument('--no_generations', type=int, default=100, help='Number of generations for optimization')
    parser.add_argument('--no_processes', type=int, default=8, help='Number of parallel processes')
    parser.add_argument('--save_as_gif', action='store_true', help='Save results as GIF')
    parser.add_argument('--output_directory', type=str, default='./output/', help='Output directory for results')
    parser.add_argument('--obj_weights', type=float, nargs=3, default=[0.5, 0, 0.5], help='Weights for the objectives [capacity_weight, odc_count_weight, avg_distance_weight]')
    args = parser.parse_args()

    start_time = time.time()
    main(args.clients_csv, args.num_initial_odcs, args.max_distance, args.max_capacity, args.cpu_per_100mhz, args.no_generations, args.no_processes, args.save_as_gif, args.output_directory, args.obj_weights)
    end_time = time.time()

    print("Elapsed time: {:.2f} seconds".format(end_time - start_time))
