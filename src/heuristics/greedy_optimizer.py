import numpy as np
from src.base_optimizer import BaseOptimizer


class GreedyOptimizer(BaseOptimizer):
    def run(self):
        num_odcs = len(self.problem.initial_odcs)
        solution = np.zeros(num_odcs)
        client_counts = np.zeros(num_odcs)

        for i, client in enumerate(self.problem.clients):
            distances = self.problem.distances[i]
            closest_odc = np.argmin(distances)
            client_counts[closest_odc] += 1

        sorted_indices = np.argsort(-client_counts)
        for i in sorted_indices[:self.args.k]:
            solution[i] = 1

        solution = solution.reshape(1, -1)
        F, G = self.problem.evaluate(solution, return_values_of=["F", "G"])
        objectives = F[0]
        constraints = G[0]

        self.tracker.update(solution[0], objectives)

        return self.format_solution(
            solution=solution[0],
            objectives=objectives,
            constraints=constraints,
            name="Greedy"
        )