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
#from pymoo.util.termination.default import SingleObjectiveDefaultTermination
from pymoo.termination.default import DefaultSingleObjectiveTermination
#from pymoo.util.display import Display
from functools import partial
import math  # Add this import
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

        # Maximize total capacity , i.e. no of CPU cores per ODC
        weighted_total_capacity = -total_capacities * self.obj_weights[0]

        # Minimize no. of active ODCs, i.e. no. of ODCs processing the baseband for O-RUs
        weighted_num_active_odcs = num_active_odcs * self.obj_weights[1]

        # Minimize the avg. O-RU <-> ODC distance
        weighted_avg_distances = avg_distances * self.obj_weights[2]

        out["F"] = np.column_stack([weighted_total_capacity, weighted_num_active_odcs, weighted_avg_distances])
        out["G"] = constraints

# Plotting function with map and CDFs
def plot_solution(clients, best_odcs, client_associations, capacities, max_distance, max_capacity, gen, num_trials):
    fig = plt.figure(figsize=(26, 10))
    gs = gridspec.GridSpec(5, 13, figure=fig)

    ax_map = fig.add_subplot(gs[:, 0:3])
    ax_text = fig.add_subplot(gs[0, 4:])
    ax_cdf_cpu = fig.add_subplot(gs[1:4, 4:6])
    ax_cdf_orus = fig.add_subplot(gs[1:4, 7:9])
    ax_cdf_distance = fig.add_subplot(gs[1:4, 10:12])

    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    client_lat_lon = np.array([[client["longitude"], client["latitude"]] for client in clients])
    odc_lat_lon = np.array([[odc[1], odc[0]] for odc in best_odcs])
    all_points = np.vstack([client_lat_lon, odc_lat_lon])
    all_points_merc = np.array([transformer.transform(x, y) for x, y in all_points])

    client_points_merc = all_points_merc[:len(clients)]
    odc_points_merc = all_points_merc[len(clients):]

    ax_map.scatter(client_points_merc[:, 0], client_points_merc[:, 1], color='blue', label='O-RU Clients')
    ax_map.scatter(odc_points_merc[:, 0], odc_points_merc[:, 1], color='red', label='ODCs')

    for client_id, odc in client_associations:
        client = next(c for c in clients if c['oru_id'] == client_id)
        client_merc = transformer.transform(client["longitude"], client["latitude"])
        odc_merc = transformer.transform(odc[1], odc[0])
        ax_map.plot([client_merc[0], odc_merc[0]], [client_merc[1], odc_merc[1]], 'k--', alpha=0.5)
        ax_map.text(client_merc[0], client_merc[1], f"O-RU {client['oru_id']}", fontsize=10, ha='right')

    for odc in best_odcs:
        odc_merc = transformer.transform(odc[1], odc[0])
        ax_map.text(odc_merc[0], odc_merc[1], f"ODC {best_odcs.index(odc)+1}", fontsize=12, ha='right')

    buffer = 1000

    ax_map.set_xlim(all_points_merc[:, 0].min() - buffer, all_points_merc[:, 0].max() + buffer)
    ax_map.set_ylim(all_points_merc[:, 1].min() - buffer, all_points_merc[:, 1].max() + buffer)

    ctx.add_basemap(ax_map, source=ctx.providers.OpenStreetMap.Mapnik)

    ax_map.set_xlabel('Longitude')
    ax_map.set_ylabel('Latitude')
    ax_map.set_title(f"O-RU Clients and ODC Locations (Generation {gen+1}/{num_trials})")
    ax_map.legend(loc='upper left')  # Fixed location for legend
    ax_map.grid(True)

    ax_text.text(0.5, 0.5, f"Total number of ODCs: {len(best_odcs)}", ha='center', va='center', fontsize=16)
    ax_text.axis('off')

    cpu_counts = sorted([capacity for capacity in capacities.values()])
    cdf_cpu = np.arange(1, len(cpu_counts) + 1) / len(cpu_counts)
    ax_cdf_cpu.set_xlim(0, max_capacity)
    ax_cdf_cpu.set_ylim(0, 1)
    ax_cdf_cpu.plot(cpu_counts, cdf_cpu, marker='.', linestyle='-')
    ax_cdf_cpu.set_xlabel('Number of CPUs')
    ax_cdf_cpu.set_ylabel('CDF')
    ax_cdf_cpu.set_title('CDF of Number of CPUs per ODC')
    ax_cdf_cpu.grid(True)

    oru_counts = sorted([sum(1 for assoc in client_associations if assoc[1] == odc) for odc in best_odcs])
    cdf_orus = np.arange(1, len(oru_counts) + 1) / len(oru_counts)
    max_orus = max(oru_counts) if oru_counts else 0  # Determine the max value for x-axis
    ax_cdf_orus.set_xlim(0, max_orus)  # Set x-axis limit based on max_orus
    ax_cdf_orus.set_ylim(0, 1)
    ax_cdf_orus.plot(oru_counts, cdf_orus, marker='.', linestyle='-')
    ax_cdf_orus.set_xlabel('Number of O-RUs')
    ax_cdf_orus.set_ylabel('CDF')
    ax_cdf_orus.set_title('CDF of Number of O-RUs per ODC')
    ax_cdf_orus.grid(True)

    individual_distances = haversine_np(client_lat_lon[:, 1], client_lat_lon[:, 0], np.array([odc[0] for _, odc in client_associations]), np.array([odc[1] for _, odc in client_associations]))
    individual_distances_sorted = np.sort(individual_distances)
    cdf_distances = np.arange(1, len(individual_distances_sorted) + 1) / len(individual_distances_sorted)
    ax_cdf_distance.set_xlim(0, max_distance)
    ax_cdf_distance.set_ylim(0, 1)
    ax_cdf_distance.plot(individual_distances_sorted, cdf_distances, marker='.', linestyle='-')
    ax_cdf_distance.set_xlabel('Distance (km)')
    ax_cdf_distance.set_ylabel('CDF')
    ax_cdf_distance.set_title('CDF of Distances between O-RUs and ODCs')
    ax_cdf_distance.grid(True)

    fig.tight_layout()
    return fig

def assign_clients_to_odcs_using_precomputed_distances(clients, selected_odcs, distances, initial_odcs):
    capacities = {odc: 0 for odc in selected_odcs}
    fiberlength = {odc: 0 for odc in selected_odcs}
    client_associations = []
    odc_indices = [i for i, odc in enumerate(initial_odcs) if odc in selected_odcs]
    #print(len(selected_odcs))
    for i, client in enumerate(clients):
        if selected_odcs:
            selected_distances = distances[i, odc_indices]
            #print(len(selected_distances))
            closest_odc_idx = np.argmin(selected_distances)
            #print(closest_odc_idx)
            closest_odc = selected_odcs[closest_odc_idx]
            capacities[closest_odc] += client["cpu_cores"]
            client_associations.append((client["oru_id"], closest_odc))
            fiberlength[closest_odc] += selected_distances[closest_odc_idx]

    return capacities, client_associations,fiberlength

# Example usage in the generate_frame function
def generate_frame(gen, num_trials, solution, clients, max_distance, max_capacity, initial_odcs, distances):
    selected_indices = [i for i, x in enumerate(solution) if x > 0.5]
    if not selected_indices:
        return None  # Skip if no ODCs are selected
    selected_odcs = [initial_odcs[i] for i in selected_indices]
    #print(selected_indices)

    capacities, client_associations,_ = assign_clients_to_odcs_using_precomputed_distances(clients, selected_odcs, distances, initial_odcs)
    active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
    selected_odcs = [odc for odc in selected_odcs if odc in active_odcs]
    client_associations = [(client_id, odc) for client_id, odc in client_associations if odc in active_odcs]

    # Generate the plot
    fig = plot_solution(clients, selected_odcs, client_associations, active_odcs, max_distance, max_capacity, gen, num_trials)
    
    # Convert the plot to an image frame
    fig.canvas.draw()
    frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype='uint8').reshape(fig.canvas.get_width_height()[::-1] + (4,))
    plt.close(fig)
    
    return frame

def precompute_distances(clients, initial_odcs):
    client_coords = np.array([(client["latitude"], client["longitude"]) for client in clients])
    odc_coords = np.array(initial_odcs)
    num_clients = len(clients)
    num_odcs = len(initial_odcs)
    
    distances = np.zeros((num_clients, num_odcs))
    for i in range(num_clients):
        distances[i, :] = haversine_np(
            np.full(num_odcs, client_coords[i, 0]),
            np.full(num_odcs, client_coords[i, 1]),
            odc_coords[:, 0],
            odc_coords[:, 1]
        )
    return distances

class BestSolutionTracker:
    def __init__(self, obj_weights):
        self.best_solutions = []
        self.obj_weights = obj_weights

    def update(self, algorithm):
        try:
            # Calculate a composite score for each solution in the population
            composite_scores = (
                algorithm.pop.get("F")[:, 0] * self.obj_weights[0] +
                algorithm.pop.get("F")[:, 1] * self.obj_weights[1] +
                algorithm.pop.get("F")[:, 2] * self.obj_weights[2]
            )
            # Find the index of the best solution based on the composite score
            best_idx = np.argmin(composite_scores)
            best_solution = algorithm.pop.get("X")[best_idx]
            self.best_solutions.append(best_solution)
        except Exception as e:
            print(f"Error in BestSolutionTracker: {e}")

def main():
    
    
    parser = argparse.ArgumentParser()
    #problem parameters
    parser.add_argument("-c", "--cpuper100", type=str,default='16',help='cpus per 100MHz')
    parser.add_argument("-d", "--maxdistance", type=str, default='3', help='Max distance')
    parser.add_argument("-cp", "--capacity", type=str,default='2560', help='Max capacity')
    parser.add_argument("-o", "--odcs", type=str, default='0',help='No. of Initial ODCs')
    #GA parameters
    parser.add_argument("-t", "--trials", type=str, default='60',help='no. of trials"')
    parser.add_argument("-pop", "--population", type=str, default='300',help='Population Size')
    parser.add_argument("-p", "--process", type=str, default='8' ,help='No. of Process')    
    # sum of weights must be 1
    parser.add_argument("-wcpu", "--wcpu", type=str, default='0',help='Weight of CPUs per ODC')
    parser.add_argument("-wodc", "--wodc", type=str, default='0', help='Weight of no. of ODCs')
    parser.add_argument("-wd", "--wd", type=str, default='1',help='Weight of ORU-ODC distance')    
    #Sim parameters
    parser.add_argument("-s", "--seed", type=str, default='1',help='Random State Seed')
    parser.add_argument("-opd", "--outputDir", type=str, default='/home/ubuntu/',help='Full path where the results will be saved')

    args = parser.parse_args()
    cpu_per_100mhz=int(args.cpuper100)
    max_distance = int(args.maxdistance)
    max_capacity = int(args.capacity)
    num_initial_odcs = int(args.odcs)
    num_trials= int(args.trials)
    population_size = int(args.population)
    no_processes = int(args.process)
    obj_weights = [float(args.wcpu), float(args.wodc), float(args.wd)]
    seed = int(args.seed)
    outputDir = args.outputDir
    
    print("#### Sim Parameters ####")
    print("## Problem Parameters ##")
    print("     cpu_per_100mhz: ", cpu_per_100mhz)
    print("     max_distance: ", max_distance)
    print("     max_capacity: ", max_capacity)
    print("     num_initial_odcs (if 0 means ODCs = RUs): ", num_initial_odcs)
    print("## NSGAII Parameters ##")
    print("     num_trials: ", num_trials)
    print("     population_size: ", population_size)
    print("     no_processes: ", no_processes)
    print("     obj_weights: ", obj_weights)
    print("## Sim Parameters ##")
    print("     seed: ", seed)
    print("     outputDir: ", outputDir)
    print("########################")
    
    ## Set Parameters
    start_time = time.time()

    #cpu_per_100mhz = 16
    #max_distance = 20 # km
    #max_capacity = 2560 # cores per O
    #num_trials = 60  # Changed to 4 for testing
    #population_size = 300 # unit?
    #no_processes = 8
    #num_initial_odcs = 50  # Define the number of initial ODCs
    #obj_weights = [0, 1, 0]  # 40% to maximize no. of CPUs per ODC, 40% for minimizing the no. of ODCs, 20% for minimizing the O-RU <-> ODC distance
    
    ## Read and preprocess datasets
    clients = read_clients('manaus.csv', cpu_per_100mhz) # create dataset
    if num_initial_odcs == 0:
        num_initial_odcs = len(clients)# ODCs = O-RUs
    initial_odcs= generate_initial_odcs(clients, num_initial_odcs) #get initial locations (lat, lon) of ODCs, based on kmeans 
    distances = precompute_distances(clients, initial_odcs) # distances between ODC and O-RU locations based on haversine formula, where the the earth curvature is considered
  
    ## Create the Problem
    # the evaluate function works along with evaluate_trial function in the minimize method
    problem = ODCPlacementProblem(clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_processes, distances, obj_weights)
    # define which algorithm will be used to minimize, this case the NSGA2 
    algorithm = NSGA2(pop_size=population_size)

    #     
    best_solution_tracker = BestSolutionTracker(obj_weights)

    def custom_callback(algorithm):
        best_solution_tracker.update(algorithm)
        
    res = minimize(problem, algorithm, termination=('n_gen', num_trials), seed=seed, verbose=True, callback=custom_callback)

    best_solutions_per_generation = best_solution_tracker.best_solutions
    
    if not best_solutions_per_generation:
        print("No best solutions were found during the optimization process.")
        return

    print(f"Total generations with best solutions: {len(best_solutions_per_generation)}")
    
    # Verify if the number of generations matches num_trials
    if len(best_solutions_per_generation) != num_trials:
        print(f"Warning: Expected {num_trials} solutions, but found {len(best_solutions_per_generation)}")

    # Create a tqdm progress bar for GIF generation
    with tqdm(total=len(best_solutions_per_generation), desc="Generating GIF") as pbar:
        with ProcessPoolExecutor(max_workers=no_processes) as executor:
            futures = [executor.submit(generate_frame, gen, num_trials, solution, clients, max_distance, max_capacity, initial_odcs, distances) for gen, solution in enumerate(best_solutions_per_generation)]
            for future in futures:
                frame = future.result()
                if frame is not None:  # Skip if no frame is generated
                    frames.append(frame)
                pbar.update(1)

    # Plot the final solution (best of the last generation)
    best_solution = best_solutions_per_generation[-1]
    selected_indices = [i for i, x in enumerate(best_solution) if x > 0.5] #solution vector has values between 0 and 1, 0.5 seems to be a intermediate standard value for this problem
    selected_odcs = [initial_odcs[i] for i in selected_indices]

    capacities, client_associations,fiberlength = assign_clients_to_odcs_using_precomputed_distances(clients, selected_odcs, distances, initial_odcs)
    #active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
    active_odcs = {
        odc: {'capacity': capacity, 'fiberlength': fiberlength[odc]}
        for odc, capacity in capacities.items()
        if capacity > 0
        }   
    selected_odcs = [odc for odc in selected_odcs if odc in active_odcs]
    client_associations = [(client_id, odc) for client_id, odc in client_associations if odc in active_odcs]
    

    print("ODC Locations and Capacities:")
    for odc, values in active_odcs.items():
        print(f"ODC {selected_odcs.index(odc)+1} Location: ({odc[0]}, {odc[1]}), Capacity: {values['capacity']} cores, Fiber: {values['fiberlength']} km")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.2f} seconds")


    #imageio.mimsave('optimization_process.gif', frames, fps=2)
    
    os.makedirs(outputDir+"/data", exist_ok=True)
    
    df_client_association = pd.DataFrame(client_associations,columns=['oru','odc_location'])
    df_capacities = pd.DataFrame(capacities.items(),columns=['odc_locations','capacities'])
    df_fiberlength = pd.DataFrame(fiberlength.items(),columns=['odc_locations','fiberlength'])
    
    df_client_association.to_csv(outputDir+"/data/"+"df_client_association"+".csv")
    df_capacities.to_csv(outputDir+"/data/"+"df_capacities"+".csv")
    df_fiberlength.to_csv(outputDir+"/data/"+"df_fiberlength"+".csv")
    
    imageio.mimsave(outputDir+"/data/"+'optimization_process.gif', frames, fps=2)

if __name__ == "__main__":
    main()
