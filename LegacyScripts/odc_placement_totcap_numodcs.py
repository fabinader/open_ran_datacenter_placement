import numpy as np
from deap import algorithms, base, creator, tools, benchmarks
import random
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec  # Import gridspec
import pandas as pd
import locale
import contextily as ctx
from pyproj import Proj, Transformer
import multiprocessing
import time
import imageio

# Set locale to ensure dot-separated decimal representation
locale.setlocale(locale.LC_NUMERIC, 'C')  # Use 'C' locale which is independent of any specific locale settings

frames = []

# Haversine distance calculation function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# Function to extract bandwidth from ITU standard for radio emission designations
def extract_bandwidth(designation):
    # Define a dictionary for unit conversion
    unit_dict = {
        'H': 1e-6,    # Hertz to Megahertz
        'K': 1e-3,    # Kilohertz to Megahertz
        'M': 1,       # Megahertz to Megahertz
        'G': 1e3      # Gigahertz to Megahertz
    }
    
    # Extract the part containing the numeric bandwidth and its unit
    # Find the position of the unit character (H, K, M, G)
    for i, char in enumerate(designation):
        if char in unit_dict:
            numeric_part = designation[:i]
            unit = char
            break
    
    # Convert to float and apply unit conversion
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

# Fitness evaluation function for multi-objective optimization
def evaluate(individual, clients, max_distance, max_capacity):
    odcs = set(individual)
    capacities = {odc: 0 for odc in odcs}
    for client in clients:
        closest_odc = min(odcs, key=lambda odc: haversine(client["latitude"], client["longitude"], odc[0], odc[1]))
        capacities[closest_odc] += client["cpu_cores"]

    # Constraint: Distance and capacity
    valid = all(haversine(client["latitude"], client["longitude"], odc[0], odc[1]) <= max_distance for client, odc in zip(clients, individual))
    valid = valid and all(capacity <= max_capacity for capacity in capacities.values())

    if not valid:
        return float('inf'), float('inf')

    total_capacity = sum(capacities.values())
    num_odcs = len(odcs)

    return total_capacity, num_odcs

# Logging function to print statistics
def log_statistics(gen, stats):
    print(f"Generation: {gen}")
    for key, value in stats.items():
        print(f"  {key}: {value}")

# Function to generate frames in a separate process
def generate_frame(gen, num_generations, max_distance, max_capacity, max_o_rus_per_odu, args):
    clients, best_individual, odc_id_map, client_associations, active_odcs = args
    try:
        fig = plot_solution(clients, best_individual, odc_id_map, client_associations, active_odcs, gen, num_generations, max_distance, max_capacity, max_o_rus_per_odu)
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype='uint8').reshape(fig.canvas.get_width_height()[::-1] + (4,))
    except Exception as e:
        print(f"Error in generating frame for generation {gen}: {e}")
        return None
    finally:
        plt.close(fig)  # Ensure the figure is closed after creating the frame
    return frame

# Genetic Algorithm setup for multi-objective optimization
def setup_ga(clients, max_distance, max_capacity, max_o_rus_per_odu, num_generations=100, population_size=300, no_processes=1):
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0))
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("attr_odc", lambda: (random.choice(clients)["latitude"], random.choice(clients)["longitude"]))
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_odc, len(clients))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)
    toolbox.register("select", tools.selNSGA2)
    
    # Create a multiprocessing pool
    pool = multiprocessing.Pool(processes=no_processes)
    toolbox.register("map", pool.map)
    
    toolbox.register("evaluate", evaluate, clients=clients, max_distance=max_distance, max_capacity=max_capacity)

    population = toolbox.population(n=population_size)

    # Define statistics to track progress
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    # Define hall of fame to store the best individuals
    hof = tools.HallOfFame(1)

    frame_pool = multiprocessing.Pool(processes=1)
    results = []

    for gen in range(num_generations):
        algorithms.eaMuPlusLambda(population, toolbox, mu=population_size, lambda_=population_size, cxpb=0.7, mutpb=0.3, ngen=1, stats=stats, halloffame=hof, verbose=True)

        # Get the best individual after this generation
        best_individual = hof[0]
        odcs = set(best_individual)
        capacities = {odc: 0 for odc in odcs}
        client_associations = []

        # Assign unique IDs to each ODC
        odc_id_map = {odc: idx+1 for idx, odc in enumerate(odcs)}

        for client in clients:
            closest_odc = min(odcs, key=lambda odc: haversine(client["latitude"], client["longitude"], odc[0], odc[1]))
            capacities[closest_odc] += client["cpu_cores"]
            client_associations.append((client["oru_id"], closest_odc, odc_id_map[closest_odc]))

        # Filter out ODCs with no allocated CPUs
        active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
        odc_id_map = {odc: odc_id for odc, odc_id in odc_id_map.items() if odc in active_odcs}
        client_associations = [(client_id, odc, odc_id) for client_id, odc, odc_id in client_associations if odc in active_odcs]

        # Update best_individual to only include active ODCs
        best_individual = [odc for odc in best_individual if odc in active_odcs]

        # Prepare arguments for the frame generation function
        frame_args = (clients, best_individual, odc_id_map, client_associations, active_odcs)
        result = frame_pool.apply_async(generate_frame, (gen, num_generations, max_distance, max_capacity, max_o_rus_per_odu, frame_args,))
        results.append(result)

    frame_pool.close()
    frame_pool.join()

    for result in results:
        frame = result.get()
        if frame is not None:
            frames.append(frame)

    return population, hof

# Plotting function with map and CDFs
def plot_solution(clients, best_individual, odc_id_map, client_associations, active_odcs, gen, total_gen, max_distance, max_capacity, max_o_rus_per_odu):
    fig = plt.figure(figsize=(26, 10))
    gs = gridspec.GridSpec(5, 13, figure=fig)

    # Create the subplots with specified positions and sizes
    ax_map = fig.add_subplot(gs[:, 0:3])  # Span all rows in the first four columns
    ax_text = fig.add_subplot(gs[0, 4:])  # Span the first row in the remaining columns
    ax_cdf_cpu = fig.add_subplot(gs[1:4, 4:6])  # Second row, third column
    ax_cdf_orus = fig.add_subplot(gs[1:4, 7:9])  # Second row, fourth column
    ax_cdf_distance = fig.add_subplot(gs[1:4, 10:12])  # Third row, span the last two columns

    odcs = list(set(best_individual))

    # Transform coordinates to Web Mercator using Transformer
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    client_lat_lon = np.array([[client["longitude"], client["latitude"]] for client in clients])
    odc_lat_lon = np.array([[odc[1], odc[0]] for odc in odcs])
    all_points = np.vstack([client_lat_lon, odc_lat_lon])
    all_points_merc = np.array([transformer.transform(x, y) for x, y in all_points])

    client_points_merc = all_points_merc[:len(clients)]
    odc_points_merc = all_points_merc[len(clients):]

    ax_map.scatter(client_points_merc[:, 0], client_points_merc[:, 1], color='blue', label='O-RU Clients')
    ax_map.scatter(odc_points_merc[:, 0], odc_points_merc[:, 1], color='red', label='ODCs')

    for client_id, odc, odc_id in client_associations:
        client = next(c for c in clients if c['oru_id'] == client_id)
        client_merc = transformer.transform(client["longitude"], client["latitude"])
        odc_merc = transformer.transform(odc[1], odc[0])
        ax_map.plot([client_merc[0], odc_merc[0]], [client_merc[1], odc_merc[1]], 'k--', alpha=0.5)
        ax_map.text(client_merc[0], client_merc[1], f"O-RU {client['oru_id']}", fontsize=10, ha='right')

    for odc in odcs:
        odc_merc = transformer.transform(odc[1], odc[0])
        if odc in odc_id_map:
            ax_map.text(odc_merc[0], odc_merc[1], f"ODC {odc_id_map[odc]}", fontsize=12, ha='right')

    # Calculate buffer in meters
    buffer = 1000  # 1 kilometer buffer for map display

    ax_map.set_xlim(all_points_merc[:, 0].min() - buffer, all_points_merc[:, 0].max() + buffer)
    ax_map.set_ylim(all_points_merc[:, 1].min() - buffer, all_points_merc[:, 1].max() + buffer)

    ctx.add_basemap(ax_map, source=ctx.providers.OpenStreetMap.Mapnik)

    ax_map.set_xlabel('Longitude')
    ax_map.set_ylabel('Latitude')
    ax_map.set_title(f"O-RU Clients and ODC Locations ({gen+1}/{total_gen})")
    ax_map.legend()
    ax_map.grid(True)

    # Text for total number of ODCs
    ax_text.text(0.5, 0.5, f"Total number of ODCs: {len(active_odcs)}", ha='center', va='center', fontsize=16)
    ax_text.axis('off')

    # CDF of the number of CPUs per ODC
    cpu_counts = sorted([capacity for capacity in active_odcs.values()])
    cdf_cpu = np.arange(1, len(cpu_counts) + 1) / len(cpu_counts)
    ax_cdf_cpu.set_xlim(0,max_capacity)
    ax_cdf_cpu.set_ylim(0,1)
    ax_cdf_cpu.plot(cpu_counts, cdf_cpu, marker='.', linestyle='-')
    ax_cdf_cpu.set_xlabel('Number of CPUs')
    ax_cdf_cpu.set_ylabel('CDF')
    ax_cdf_cpu.set_title('CDF of Number of CPUs per ODC')
    ax_cdf_cpu.grid(True)

    # CDF of the number of O-RUs per ODC
    oru_counts = sorted([sum(1 for assoc in client_associations if assoc[1] == odc) for odc in active_odcs.keys()])
    cdf_orus = np.arange(1, len(oru_counts) + 1) / len(oru_counts)
    ax_cdf_orus.set_xlim(0,max_o_rus_per_odu)
    ax_cdf_orus.set_ylim(0,1)
    ax_cdf_orus.plot(oru_counts, cdf_orus, marker='.', linestyle='-')
    ax_cdf_orus.set_xlabel('Number of O-RUs')
    ax_cdf_orus.set_ylabel('CDF')
    ax_cdf_orus.set_title('CDF of Number of O-RUs per ODC')
    ax_cdf_orus.grid(True)

    # CDF of the individual distances between O-RUs and their ODCs
    individual_distances = [haversine(client["latitude"], client["longitude"], odc[0], odc[1])
                            for client_id, odc, _ in client_associations]
    individual_distances_sorted = sorted(individual_distances)
    cdf_distances = np.arange(1, len(individual_distances_sorted) + 1) / len(individual_distances_sorted)
    ax_cdf_distance.set_xlim(0,max_distance)
    ax_cdf_distance.set_ylim(0,1)
    ax_cdf_distance.plot(individual_distances_sorted, cdf_distances, marker='.', linestyle='-')
    ax_cdf_distance.set_xlabel('Distance (km)')
    ax_cdf_distance.set_ylabel('CDF')
    ax_cdf_distance.set_title('CDF of Distances between O-RUs and ODCs')
    ax_cdf_distance.grid(True)

    fig.tight_layout()
    return fig

# Main function
def main():
    """
    Main function to execute the script.
    
    This script reads O-RU client data from a CSV file, processes the data to extract necessary fields, and
    applies a Multi-Objective Facility Location Problem (MO-FLP) algorithm to determine optimal ODC placement.

    Input CSV file format (oru_clients.csv):
    - cell_site_id
    - emission_designation
    - technology (NR or LTE)
    - tx_frequency (MHz)
    - rx_frequency (MHz)
    - azimuth (degrees, 0 means omni)
    - antenna_gain (dB)
    - back_front relation (dBi, 0 means omni antenna)
    - hpa (Half Power Angle, degrees)
    - mechanical_elevation (degrees)
    - polarization (H, V, CR, CL, X)
    - antenna_height (meters, <200m)
    - tx_power (Watts)
    - latitude (degrees, dot-separated)
    - longitude (degrees, dot-separated)
    - cell_carrier_id

    Outputs:
    - Print ODC locations and their respective capacity requirements.
    - Plot of O-RU client and ODC locations, showing their relationships.
    """

    start_time = time.time()

    cpu_per_100mhz = 16  # Number of CPUs required for processing 4x4 MIMO 100 MHz
    max_distance = 20  # Industry default max distance in kilometers for fronthaul
    max_capacity = 2560  # Example max capacity in CPU cores
    num_generations = 300  # Number of GA generations
    population_size = 600  # GA population size in each generation
    no_processes = 8  # Number of processors in the processing pool for the GA parallelization
    max_o_rus_per_odu = 30  # for plotting

    clients = read_clients('manaus.csv', cpu_per_100mhz)
    population, hof = setup_ga(clients, max_distance, max_capacity, max_o_rus_per_odu, num_generations=num_generations, population_size=population_size, no_processes=no_processes)

    # Extracting the best solution
    best_individual = hof[0]
    odcs = set(best_individual)
    capacities = {odc: 0 for odc in odcs}
    client_associations = []

    # Assign unique IDs to each ODC
    odc_id_map = {odc: idx+1 for idx, odc in enumerate(odcs)}

    for client in clients:
        closest_odc = min(odcs, key=lambda odc: haversine(client["latitude"], client["longitude"], odc[0], odc[1]))
        capacities[closest_odc] += client["cpu_cores"]
        client_associations.append((client["oru_id"], closest_odc, odc_id_map[closest_odc]))

    # Filter out ODCs with no allocated CPUs
    active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
    odc_id_map = {odc: odc_id for odc, odc_id in odc_id_map.items() if odc in active_odcs}
    client_associations = [(client_id, odc, odc_id) for client_id, odc, odc_id in client_associations if odc in active_odcs]

    # Update best_individual to only include active ODCs
    best_individual = [odc for odc in best_individual if odc in active_odcs]

    # Ensure each O-RU is associated with an ODC
    for client in clients:
        if client["oru_id"] not in [assoc[0] for assoc in client_associations]:
            closest_odc = min(active_odcs.keys(), key=lambda odc: haversine(client["latitude"], client["longitude"], odc[0], odc[1]))
            client_associations.append((client["oru_id"], closest_odc, odc_id_map[closest_odc]))
            capacities[closest_odc] += client["cpu_cores"]

    # Output the ODC locations and their respective capacity requirement
    print("ODC Locations and Capacities:")
    for odc, capacity in active_odcs.items():
        print(f"ODC {odc_id_map[odc]} Location: ({odc[0]}, {odc[1]}), Capacity: {capacity} cores")

    # Output the associations of each O-RU to its ODC
    print("\nO-RU to ODC Associations:")
    for oru_id, odc, odc_id in client_associations:
        distance = haversine(next(c for c in clients if c['oru_id'] == oru_id)["latitude"], next(c for c in clients if c['oru_id'] == oru_id)["longitude"], odc[0], odc[1])
        print(f"O-RU {oru_id} is associated with ODC {odc_id} at location ({odc[0]}, {odc[1]}) with a distance of {distance:.2f} km")

    end_time = time.time()

    execution_time = end_time - start_time

    print(f"Execution time: {execution_time:.2f} seconds")

    # Plot the solution
    plot_solution(clients, best_individual, odc_id_map, client_associations, active_odcs, num_generations, num_generations, max_distance, max_capacity, max_o_rus_per_odu)

    # Save frames as a GIF
    imageio.mimsave('optimization_process.gif', frames, fps=2)  # fps=2 for 2 frames per second

if __name__ == "__main__":
    main()
