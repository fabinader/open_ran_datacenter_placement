from pymoo.algorithms.moo.nsga2 import NSGA2
import numpy as np
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from src.base_optimizer import BaseOptimizer
from src.solution_tracker import BestSolutionTracker


# class NSGA2Optimizer(BaseOptimizer):
#     def __init__(self, problem, tracker: BestSolutionTracker, args):
#         self.problem = problem
#         self.tracker = tracker
#         self.population_size = args.population_size
#         self.generations = args.num_trials
#         self.seed = args.seed

#         self.algorithm = NSGA2(pop_size=self.population_size)
#         self.termination = get_termination("n_gen", self.generations)

#     def run(self):
#         result = minimize(
#             self.problem,
#             self.algorithm,
#             termination=self.termination,
#             seed=self.seed,
#             verbose=True,
#             callback=self._callback,
#             save_history=True
#         )

#         X = result.X
#         F = result.F
#         G = result.G if hasattr(result, "G") else [[0, 0]] * len(F)

#         # Normalização dos objetivos
#         F_norm = (F - np.min(F, axis=0)) / (np.ptp(F, axis=0) + 1e-9)

#         # Pesos arbitrários (pode ser customizado)
#         weights = np.array([0.5, 0.5])

#         # Score por soma ponderada dos objetivos normalizados
#         scores = np.dot(F_norm, weights)

#         best_idx = int(np.argmin(scores))

#         return self.format_solution(
#             solution=X[best_idx].tolist(),
#             objectives=F[best_idx].tolist(),
#             constraints=G[best_idx].tolist(),
#             name="NSGA2",
#             plot=result
#         )

#     def _callback(self, algorithm):
#         self.tracker.update_from_population(algorithm)

# src/heuristics/nsga2_optimizer.py

class NSGA2Optimizer(BaseOptimizer):
    def __init__(self, problem, tracker, args):
        self.problem = problem
        self.population_size = args.population_size
        self.generations = args.num_trials
        self.seed = args.seed

        self.algorithm = NSGA2(pop_size=self.population_size)
        self.termination = get_termination("n_gen", self.generations)

    def run(self):
        result = minimize(
            self.problem,
            self.algorithm,
            termination=self.termination,
            seed=self.seed,
            verbose=True,
            save_history=True,
        )

        # Retorna todas as soluções da Fronteira de Pareto
        return {
            "pareto_solutions": result.X,
            "pareto_objectives": result.F,
            "constraints": result.G if hasattr(result, "G") else None,
            "name": "NSGA2",
            "plot": result  # para gráficos, convergência etc.
        }