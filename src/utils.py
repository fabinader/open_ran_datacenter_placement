import numpy as np
import pandas as pd
import locale
import warnings
import math
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import KMeans
import re


# Set locale to ensure dot-separated decimal representation
locale.setlocale(locale.LC_NUMERIC, 'C')


class Utils:
    @staticmethod
    def haversine_np(lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in kilometers
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    @staticmethod
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

    @staticmethod
    def calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz):
        return (bandwidth_mhz / 100) * cpu_per_100mhz

    @staticmethod
    def read_clients(file_path, cpu_per_100mhz):
        df = pd.read_csv(file_path, converters={
            'latitude': locale.atof,
            'longitude': locale.atof
        })

        clients = []
        for index, row in df.iterrows():
            bandwidth_mhz = Utils.extract_bandwidth(row['emission_designation'])
            cpu_cores = Utils.calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz)
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

    @staticmethod
    def generate_initial_odcs(clients, num_initial_odcs, seed):
        if num_initial_odcs == 0:
            num_initial_odcs = len(clients)  # ODCs = O-RUs

        distinct_clusters = 0
        n_clusters = 0
        lat_lon = np.array([[c["latitude"], c["longitude"]] for c in clients])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ConvergenceWarning)
            kmeans = KMeans(n_clusters=num_initial_odcs, random_state=seed).fit(lat_lon)
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
                    kmeans = KMeans(n_clusters=distinct_clusters, random_state=seed).fit(lat_lon)
                    initial_odcs = kmeans.cluster_centers_
                else:
                    print("Could not extract the required numbers from the warning message.")
            else:
                print("No ConvergenceWarning")

        return [(lat, lon) for lat, lon in initial_odcs]

    @staticmethod
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
    
    @staticmethod
    def assign_clients_to_odcs_using_precomputed_distances(clients, selected_odcs, distances, initial_odcs):
        capacities = {odc: 0 for odc in selected_odcs}
        fiberlength = {odc: 0 for odc in selected_odcs}
        client_associations = []
        odc_indices = [i for i, odc in enumerate(initial_odcs) if odc in selected_odcs]

        # print(len(selected_odcs))
        for i, client in enumerate(clients):
            if selected_odcs:
                selected_distances = distances[i, odc_indices]
                # print(len(selected_distances))
                closest_odc_idx = np.argmin(selected_distances)
                # print(closest_odc_idx)
                closest_odc = selected_odcs[closest_odc_idx]
                capacities[closest_odc] += client["cpu_cores"]
                client_associations.append((client["oru_id"], closest_odc))
                fiberlength[closest_odc] += selected_distances[closest_odc_idx]

        return capacities, client_associations, fiberlength
    
    @staticmethod
    def precompute_distances(clients, initial_odcs):
        client_coords = np.array([(client["latitude"], client["longitude"]) for client in clients])
        odc_coords = np.array(initial_odcs)
        num_clients = len(clients)
        num_odcs = len(initial_odcs)
        
        distances = np.zeros((num_clients, num_odcs))
        for i in range(num_clients):
            distances[i, :] = Utils.haversine_np(
                np.full(num_odcs, client_coords[i, 0]),
                np.full(num_odcs, client_coords[i, 1]),
                odc_coords[:, 0],
                odc_coords[:, 1]
            )

        return distances