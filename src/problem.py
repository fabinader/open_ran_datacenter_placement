from pymoo.core.problem import Problem
import numpy as np
from functools import partial
from concurrent.futures import ProcessPoolExecutor
from src.utils import Utils


class ODCPlacementProblem(Problem):
    def __init__(self, clients, initial_odcs, max_distance, max_capacity, cpu_per_100mhz, no_processes, distances):
        self.clients = clients
        self.initial_odcs = initial_odcs
        self.max_distance = max_distance
        self.max_capacity = max_capacity
        self.cpu_per_100mhz = cpu_per_100mhz
        self.no_processes = no_processes
        self.distances = distances

        super().__init__(
            n_var=len(initial_odcs),
            n_obj=2,  # Apenas dois objetivos
            n_constr=2,  # Restrições: capacidade e distância
            xl=0,
            xu=1
        )

    def _evaluate(self, X, out, *args, **kwargs):
        n_trials = X.shape[0]

        total_capacities = np.zeros(n_trials)
        avg_distances = np.zeros(n_trials)
        constraints = np.zeros((n_trials, 2))

        evaluate_trial_partial = partial(
            Utils.evaluate_trial,
            X=X,
            clients=self.clients,
            initial_odcs=self.initial_odcs,
            max_distance=self.max_distance,
            max_capacity=self.max_capacity,
            distances=self.distances
        )

        with ProcessPoolExecutor(max_workers=self.no_processes) as executor:
            results = list(executor.map(evaluate_trial_partial, range(n_trials)))

        for i, (constraint0, constraint1, total_capacity, _, avg_distance) in enumerate(results):
            constraints[i, 0] = constraint0
            constraints[i, 1] = constraint1
            total_capacities[i] = total_capacity
            avg_distances[i] = avg_distance

        # Objetivo 1: maximizar capacidade alocada (convertido em minimização)
        f1 = -total_capacities

        # Objetivo 2: minimizar distância média
        f2 = avg_distances

        out["F"] = np.column_stack([f1, f2])
        out["G"] = constraints