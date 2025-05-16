from src.config import SimulationConfig
from src.utils import Utils
# from src.heuristics.nsga2_optimizer import NSGA2Optimizer
# from src.heuristics.random_optimizer import RandomOptimizer
# from src.heuristics.greedy_optimizer import GreedyOptimizer
# from src.heuristics.kmeans_optimizer import KMeansOptimizer
# from src.runner import run_all_heuristics
# from src.save_results import SaveResults
# from visualization.generate_gif import GenerateGIF
# from visualization.plot_results import ODCPlotter
# from visualization.plot_convergence import ConvergencePlot
# from visualization.plot_pareto_front import plot_pareto_front

import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
import matplotlib.pyplot as plt

class ODCPlacementProblem(Problem):
    def __init__(self, clients, odcs, distances, max_distance, max_capacity):
        self.clients = clients
        self.odcs = odcs
        self.distances = distances
        self.max_distance = max_distance
        self.max_capacity = max_capacity

        self.n_clients = len(clients)
        self.n_odcs = len(odcs)

        # demands and capacity
        self.demands = np.array([cl['cpu_cores'] for cl in clients])
        self.capacities = np.full(self.n_odcs, self.max_capacity)   # exemplo fixo, pode ser diferente por ODC

        # Domínio inteiro: cada cliente é atribuído a um índice de ODC
        super().__init__(
            n_var=self.n_clients,
            n_obj=2,
            n_constr=self.n_odcs + self.n_clients,
            xl=0,
            xu=self.n_odcs - 1,
            elementwise_evaluation=True
        )

    def _evaluate(self, x, out, *args, **kwargs):
        assignment = np.array(x)
        f1 = 0  # capacidade total alocada
        f2 = 0  # distância total

        odc_loads = np.zeros(self.n_odcs)
        distance_violations = np.zeros(self.n_clients)

        for o in range(self.n_clients):
            c = int(assignment[o])  # Garante que c seja um índice inteiro
            odc_loads[c] += self.demands[o]
            d = self.distances[o, c]  # Acessa a distância correta no array NumPy
            f1 += self.demands[o]
            f2 += d
            distance_violations[o] = d - self.max_distance

        # Restrições
        g = np.concatenate([
            odc_loads - self.capacities,      # violação de capacidade por ODC
            distance_violations               # violação de distância por O-RU
        ])

        out["F"] = [-f1, f2]
        out["G"] = g


def main():
    # 1. Load Configurations
    args = SimulationConfig()

    # 2. Load Data
    clients = Utils.read_clients(args.dataset, args.cpu_per_100mhz)

    # Generate initial ODCs
    initial_odcs = Utils.generate_initial_odcs(clients, args.num_initial_odcs, args.seed)

    # Distance precomputation
    distances = Utils.precompute_distances(clients, initial_odcs)
    # print("Tipo de 'distances':", type(distances))
    # if isinstance(distances, list):
    #     print("Tipo do primeiro elemento de 'distances':", type(distances[0]))
    #     if isinstance(distances[0], list):
    #         print("Tipo do primeiro elemento da primeira lista em 'distances':", type(distances[0][0]))

    problem = ODCPlacementProblem(clients, initial_odcs, distances, args.max_distance, args.max_capacity)

    algorithm = NSGA2(
        pop_size=args.population_size,
        sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )

    termination = get_termination("n_gen", 200)

    res = minimize(
        problem,
        algorithm,
        termination,
        seed=args.seed,
        save_history=True,
        verbose=True
    )

    print("Frente de Pareto:")
    print(res.F)

    # Visualizando a frente de Pareto
    plt.figure(figsize=(8, 6))
    plt.scatter(res.F[:, 0], res.F[:, 1], marker="o", color="blue", s=40)
    plt.title("Frente de Pareto Obtida pelo NSGA-II (ZDT1)")
    plt.xlabel("f1(x)")
    plt.ylabel("f2(x)")
    plt.grid(True)
    plt.show()

    # 3. Creates the problem
    # problem = ODCPlacementProblem(
    #     clients=clients,
    #     initial_odcs=initial_odcs,
    #     max_distance=args.max_distance,
    #     max_capacity=args.max_capacity,
    #     cpu_per_100mhz=args.cpu_per_100mhz,
    #     no_processes=args.no_processes,
    #     distances=distances,
    #     # obj_weights=args.obj_weights
    # )

    # heuristics = {
    #     "NSGA2": NSGA2Optimizer,
    #     # "Random": RandomOptimizer,
    #     # "Greedy": GreedyOptimizer,
    #     # "KMeans": KMeansOptimizer
    # }

    # results = run_all_heuristics(heuristics, problem, args)

    # SaveResults.save(results, problem)

    # if "NSGA2" in results and results["NSGA2"]["result"] is not None:
    #     pareto_F = results["NSGA2"]["result"]["pareto_objectives"]
    #     plot_pareto_front(pareto_F, label="NSGA2", save_path="output/nsga2/pareto_nsga2.png")


    # plot_comparative_metrics(results=results,  obj_labels=["f1", "f2", "f3"])

    # Pega o resultado do NSGA2
    # nsga2_tracker = results["NSGA2"]["tracker"]
    # nsga2_result = results["NSGA2"]["result"]

    # Pega o resultado do Random
    # random_tracker = results["Random"]["tracker"]
    # random_result = results["Random"]["result"]

    # 6. Validation of the results
    # nsga2_tracker.validation(args.num_trials)
    # random_tracker.validation(args.num_trials)

    # 7. Generate GIF
    # GenerateGIF.generate_results(
    #     gif=args.gif,
    #     tracker=nsga2_tracker,
    #     no_processes=args.no_processes,
    #     clients=clients,
    #     max_distance=args.max_distance,
    #     max_capacity=args.max_capacity,
    #     initial_odcs=initial_odcs,
    #     distances=distances,
    # )

    # 8. Plot results
    # plotter = ODCPlotter(debug=0)
    # plotter.plot(result=nsga2_result, initial_odcs=initial_odcs, clients=clients, tracker=nsga2_tracker)

    # 9. Convergence plot
    # convergence = ConvergencePlot()
    # convergence.plot(result=nsga2_result)

    # 10. Plot NSGA-II best solution
    # plotter_best_solution = BestSolution()
    # plotter_best_solution.plot(tracker=nsga2_tracker, initial_odcs=initial_odcs, clients=clients, distances=distances)

if __name__ == "__main__":
    main()