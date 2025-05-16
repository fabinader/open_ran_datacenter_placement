import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
import contextily as ctx


class ODCPlotter:
    def __init__(self, debug=0):
        self.debug = debug

    def plot(self, result, initial_odcs, clients, tracker):
        if self.debug:
            for trial in range(len(result["plot"].X)):
                self._plot_results1(result, initial_odcs, clients, trial)
        else:
            self._plot_results2(result, initial_odcs, clients, tracker.best_idx)

    def _plot_results1(self, result, initial_odcs, clients, trial):
        plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 2, width_ratios=[3, 1])

        ax_map = plt.subplot(gs[:, 0])
        ax_obj = plt.subplot(gs[0, 1])
        ax_hist = plt.subplot(gs[1, 1])

        # Map plot
        latitudes = [client['latitude'] for client in clients]
        longitudes = [client['longitude'] for client in clients]
        ax_map.scatter(longitudes, latitudes, c='blue', label='Clients')

        selected_odcs = [initial_odcs[i] for i in range(len(initial_odcs)) if result["plot"].X[trial, i] > 0.5]
        odc_latitudes = [odc[0] for odc in selected_odcs]
        odc_longitudes = [odc[1] for odc in selected_odcs]
        ax_map.scatter(odc_longitudes, odc_latitudes, c='red', marker='x', label='Selected ODCs')

        ax_map.set_title('ODC Placement Map')
        ax_map.set_xlabel('Longitude')
        ax_map.set_ylabel('Latitude')
        ax_map.legend()

        try:
            ctx.add_basemap(ax_map, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"Error adding basemap: {e}")
            ax_map.set_facecolor('lightgray')

        # Objective values plot
        f1 = result.F[:, 0]
        f2 = result.F[:, 1]
        f3 = result.F[:, 2]
        ax_obj.plot(f1, label='Normalized Capacity')
        ax_obj.plot(f2, label='Normalized Number of ODCs')
        ax_obj.plot(f3, label='Normalized Avg Distance')
        ax_obj.set_title('Objective Values')
        ax_obj.legend()

        # Convergence history plot
        n_evals = np.arange(1, len(result.history) + 1)
        opt = [e.opt[0].F for e in result.history]
        ax_hist.plot(n_evals, opt)
        ax_hist.set_title('Convergence History')
        ax_hist.set_xlabel('Generation')
        ax_hist.set_ylabel('Objective Function Value')

        plt.tight_layout()
        output_file = os.path.join('./output/nsga2/', f'Odc_placement_results_trial_{trial}.png')
        plt.savefig(output_file)
        plt.show()

    def _plot_results2(self, result, initial_odcs, clients, trial):
        fig, ax_map = plt.subplots(figsize=(8, 8))

        latitudes = [client['latitude'] for client in clients]
        longitudes = [client['longitude'] for client in clients]
        ax_map.scatter(longitudes, latitudes, c='blue', label='Clients')

        if result["plot"].X is None:
            selected_odcs = initial_odcs
        else:
            selected_odcs = [initial_odcs[i] for i in range(len(initial_odcs)) if result["plot"].X[trial, i] > 0.5]
        odc_latitudes = [odc[0] for odc in selected_odcs]
        odc_longitudes = [odc[1] for odc in selected_odcs]
        ax_map.scatter(odc_longitudes, odc_latitudes, c='red', marker='x', label='Selected ODCs')

        ax_map.set_xlabel('Longitude')
        ax_map.set_ylabel('Latitude')
        ax_map.legend()

        try:
            ctx.add_basemap(ax_map, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"Error adding basemap: {e}")
            ax_map.set_facecolor('lightgray')

        plt.tight_layout()
        output_file = os.path.join('./output/nsga2/', f'odc_placement_results_trial_{trial}.png')
        plt.savefig(output_file, dpi=300)
        plt.close()