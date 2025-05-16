import numpy as np
from sklearn.cluster import KMeans
from src.base_optimizer import BaseOptimizer


class KMeansOptimizer(BaseOptimizer):
    def run(self):
        num_odcs = len(self.problem.initial_odcs)
        num_clusters = self.args.k

        client_coords = np.array([client["position"] for client in self.problem.clients])

        # Aplica o KMeans nos clientes
        kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=42)
        kmeans.fit(client_coords)
        centroids = kmeans.cluster_centers_

        # Seleciona os ODCs mais próximos aos centróides
        solution = np.zeros(num_odcs)
        odc_coords = np.array(self.problem.initial_odcs)

        for centroid in centroids:
            dists = np.linalg.norm(odc_coords - centroid, axis=1)
            closest_idx = np.argmin(dists)
            solution[closest_idx] = 1

        solution = solution.reshape(1, -1)
        F, G = self.problem.evaluate(solution, return_values_of=["F", "G"])
        objectives = F[0]
        constraints = G[0]

        self.tracker.update(solution[0], objectives)

        return self.format_solution(
            solution=solution[0],
            objectives=objectives,
            constraints=constraints,
            name="KMeans"
        )