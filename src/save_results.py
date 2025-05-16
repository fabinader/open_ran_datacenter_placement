import pandas as pd
from src.utils import Utils


class SaveResults:
    # @staticmethod
    # def save(results, problem):
    #     nsga2_tracker = results["NSGA2"]["tracker"]
    #     random_tracker = results["Random"]["tracker"]

    #     SaveResults.get_results(
    #         tracker=nsga2_tracker,
    #         initial_odcs=problem.initial_odcs,
    #         clients=problem.clients,
    #         distances=problem.distances,
    #         optimizer="nsga2"
    #     )

    #     SaveResults.get_results(
    #         tracker=random_tracker,
    #         initial_odcs=problem.initial_odcs,
    #         clients=problem.clients,
    #         distances=problem.distances,
    #         optimizer="random"
    #     )

    @staticmethod
    def save(results, problem):
        for optimizer_name, data in results.items():
            tracker = data.get("tracker")
            if tracker:
                SaveResults._get_results(
                    tracker=tracker,
                    initial_odcs=problem.initial_odcs,
                    clients=problem.clients,
                    distances=problem.distances,
                    optimizer=optimizer_name.lower()
                )

    @staticmethod
    def _get_results(tracker, initial_odcs, clients, distances, optimizer):
        best_solution = tracker.best_solutions[-1]
        selected_indices = [i for i, x in enumerate(best_solution) if x > 0.5]  # solution vector has values between 0 and 1, 0.5 seems to be a intermediate standard value for this problem
        selected_odcs = [initial_odcs[i] for i in selected_indices]

        capacities, client_associations,fiberlength = Utils.assign_clients_to_odcs_using_precomputed_distances(clients, selected_odcs, distances, initial_odcs)

        # active_odcs = {odc: capacity for odc, capacity in capacities.items() if capacity > 0}
        active_odcs = {
            odc: {'capacity': capacity, 'fiberlength': fiberlength[odc]}
            for odc, capacity in capacities.items()
            if capacity > 0
            }

        selected_odcs = [odc for odc in selected_odcs if odc in active_odcs]
        client_associations = [(client_id, odc) for client_id, odc in client_associations if odc in active_odcs]

        print("ODC Locations and Capacities:")
        for odc, values in active_odcs.items():
            print(f"ODC {selected_odcs.index(odc)+1} Location: ({odc[0]}, {odc[1]}), Capacity: {values['capacity']:.2f} cores, Fiber: {values['fiberlength']:.2f} km")

        df_client_association = pd.DataFrame([(oru, tuple(map(float, odc))) for oru, odc in client_associations],columns=['oru', 'odc_location'])
        df_capacities = pd.DataFrame([(tuple(map(float, loc)), cap) for loc, cap in capacities.items()], columns=['odc_locations', 'capacities'])
        df_fiberlength = pd.DataFrame([(tuple(map(float, loc)), fiber) for loc, fiber in fiberlength.items()],columns=['odc_locations', 'fiberlength'])

        media_capacity = df_capacities['capacities'].mean()
        media_fiberlength = df_fiberlength['fiberlength'].mean()
        print(f"\n\n=============== Resultados do {optimizer} ===============\n")
        print(f"\n- A média da coluna 'fiberlength' é: {media_fiberlength}\n")
        print(f"\n- A média da coluna 'capacities' é: {media_capacity:.2f}\n\n")

        df_client_association.to_csv(f"./output/{optimizer}/df_client_association.csv")
        df_capacities.to_csv(f"./output/{optimizer}/df_capacities.csv")
        df_fiberlength.to_csv(f"./output/{optimizer}/df_fiberlength.csv")