from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from pyproj import Transformer
import matplotlib.pyplot as plt
import contextily as ctx
import matplotlib.gridspec as gridspec
import numpy as np
import imageio

from src.utils import Utils


class GenerateGIF:
    @staticmethod
    def generate_results(gif, tracker, no_processes, clients, max_distance, max_capacity, initial_odcs, distances):
        if not gif:
            return

        frames = []
        with tqdm(total=len(tracker.best_solutions), desc="Generating GIF") as pbar:
            with ProcessPoolExecutor(max_workers=no_processes) as executor:
                futures = [
                    executor.submit(
                        GenerateGIF._generate_frame,
                        gen, solution, tracker, clients, max_distance, max_capacity, initial_odcs, distances
                    )
                    for gen, solution in enumerate(tracker.best_solutions)
                ]

                for future in futures:
                    frame = future.result()
                    if frame is not None:
                        frames.append(frame)
                    pbar.update(1)

        imageio.mimsave("./output/nsga2/Optimization_process.gif", frames, fps=2)

    @staticmethod
    def _generate_frame(gen, solution, tracker, clients, max_distance, max_capacity, initial_odcs, distances):
        selected_indices = [i for i, x in enumerate(solution) if x > 0.5]
        if not selected_indices:
            return None

        selected_odcs = [initial_odcs[i] for i in selected_indices]
        capacities, client_associations, _ = Utils.assign_clients_to_odcs_using_precomputed_distances(
            clients, selected_odcs, distances, initial_odcs
        )

        active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
        selected_odcs = [odc for odc in selected_odcs if odc in active_odcs]
        client_associations = [(client_id, odc) for client_id, odc in client_associations if odc in active_odcs]

        fig = GenerateGIF._plot_solution(clients, selected_odcs, client_associations, active_odcs,
                                        max_distance, max_capacity, gen, len(tracker.best_solutions))

        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype='uint8').reshape(fig.canvas.get_width_height()[::-1] + (4,))
        plt.close(fig)
        return frame

    @staticmethod
    def _plot_solution(clients, best_odcs, client_associations, capacities, max_distance, max_capacity, gen, num_trials):
        fig = plt.figure(figsize=(26, 10))
        gs = gridspec.GridSpec(5, 13, figure=fig)

        ax_map = fig.add_subplot(gs[:, 0:3])
        ax_text = fig.add_subplot(gs[0, 4:])
        ax_cdf_cpu = fig.add_subplot(gs[1:4, 4:6])
        ax_cdf_orus = fig.add_subplot(gs[1:4, 7:9])
        ax_cdf_distance = fig.add_subplot(gs[1:4, 10:12])

        transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
        client_lat_lon = np.array([[c["longitude"], c["latitude"]] for c in clients])
        odc_lat_lon = np.array([[odc[1], odc[0]] for odc in best_odcs])
        all_points = np.vstack([client_lat_lon, odc_lat_lon])
        all_points_merc = np.array([transformer.transform(x, y) for x, y in all_points])
        client_points_merc, odc_points_merc = all_points_merc[:len(clients)], all_points_merc[len(clients):]

        ax_map.scatter(client_points_merc[:, 0], client_points_merc[:, 1], color='blue', label='O-RU Clients')
        ax_map.scatter(odc_points_merc[:, 0], odc_points_merc[:, 1], color='red', label='ODCs')

        for client_id, odc in client_associations:
            client = next(c for c in clients if c['oru_id'] == client_id)
            client_merc = transformer.transform(client["longitude"], client["latitude"])
            odc_merc = transformer.transform(odc[1], odc[0])
            ax_map.plot([client_merc[0], odc_merc[0]], [client_merc[1], odc_merc[1]], 'k--', alpha=0.5)
            ax_map.text(client_merc[0], client_merc[1], f"O-RU {client['oru_id']}", fontsize=10, ha='right')

        for i, odc in enumerate(best_odcs):
            odc_merc = transformer.transform(odc[1], odc[0])
            ax_map.text(odc_merc[0], odc_merc[1], f"ODC {i+1}", fontsize=12, ha='right')

        buffer = 1000
        ax_map.set_xlim(all_points_merc[:, 0].min() - buffer, all_points_merc[:, 0].max() + buffer)
        ax_map.set_ylim(all_points_merc[:, 1].min() - buffer, all_points_merc[:, 1].max() + buffer)
        ctx.add_basemap(ax_map, source=ctx.providers.OpenStreetMap.Mapnik)
        ax_map.set_xlabel('Longitude')
        ax_map.set_ylabel('Latitude')
        ax_map.set_title(f"O-RU Clients and ODC Locations (Generation {gen+1}/{num_trials})")
        ax_map.legend(loc='upper left')
        ax_map.grid(True)

        ax_text.text(0.5, 0.5, f"Total number of ODCs: {len(best_odcs)}", ha='center', va='center', fontsize=16)
        ax_text.axis('off')

        cpu_counts = sorted(capacities.values())
        cdf_cpu = np.arange(1, len(cpu_counts) + 1) / len(cpu_counts)
        ax_cdf_cpu.set_xlim(0, max_capacity)
        ax_cdf_cpu.set_ylim(0, 1)
        ax_cdf_cpu.plot(cpu_counts, cdf_cpu, marker='.', linestyle='-')
        ax_cdf_cpu.set_title('CDF of Number of CPUs per ODC')
        ax_cdf_cpu.set_xlabel('Number of CPUs')
        ax_cdf_cpu.set_ylabel('CDF')
        ax_cdf_cpu.grid(True)

        oru_counts = sorted([sum(1 for assoc in client_associations if assoc[1] == odc) for odc in best_odcs])
        cdf_orus = np.arange(1, len(oru_counts) + 1) / len(oru_counts)
        ax_cdf_orus.set_xlim(0, max(oru_counts) if oru_counts else 1)
        ax_cdf_orus.set_ylim(0, 1)
        ax_cdf_orus.plot(oru_counts, cdf_orus, marker='.', linestyle='-')
        ax_cdf_orus.set_title('CDF of Number of O-RUs per ODC')
        ax_cdf_orus.set_xlabel('Number of O-RUs')
        ax_cdf_orus.set_ylabel('CDF')
        ax_cdf_orus.grid(True)

        individual_distances = Utils.haversine_np(
            client_lat_lon[:, 1], client_lat_lon[:, 0],
            np.array([odc[0] for _, odc in client_associations]),
            np.array([odc[1] for _, odc in client_associations])
        )
        individual_distances_sorted = np.sort(individual_distances)
        cdf_distances = np.arange(1, len(individual_distances_sorted) + 1) / len(individual_distances_sorted)
        ax_cdf_distance.set_xlim(0, max_distance)
        ax_cdf_distance.set_ylim(0, 1)
        ax_cdf_distance.plot(individual_distances_sorted, cdf_distances, marker='.', linestyle='-')
        ax_cdf_distance.set_title('CDF of Distances between O-RUs and ODCs')
        ax_cdf_distance.set_xlabel('Distance (km)')
        ax_cdf_distance.set_ylabel('CDF')
        ax_cdf_distance.grid(True)

        fig.tight_layout()

        return fig