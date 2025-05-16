import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.repair import Repair


# class ODCRepair(Repair):
#     def __init__(self, oru_cpu, odc_cap, max_dist, dist_matrix):
#         super().__init__()
#         self.oru_cpu = oru_cpu
#         self.odc_cap = odc_cap
#         self.max_dist = max_dist
#         self.dist = dist_matrix

#     def _do(self, problem, pop, **kwargs):
#         for individual in pop:
#             X = individual.get("X").reshape(len(self.oru_cpu), -1)

#             # Corrige múltiplas atribuições ou nenhuma
#             for i, row in enumerate(X):
#                 if np.sum(row) != 1:
#                     assigned = np.argmin(self.dist[i])  # escolha o mais próximo
#                     row[:] = 0
#                     row[assigned] = 1

#             # Verifica violação de distância
#             for i in range(X.shape[0]):
#                 for j in range(X.shape[1]):
#                     if self.dist[i][j] > self.max_dist:
#                         X[i][j] = 0

#             # Garante uma única alocação novamente
#             for i, row in enumerate(X):
#                 if np.sum(row) == 0:
#                     # Escolhe ODC mais próximo dentro do limite de distância
#                     candidates = np.where(self.dist[i] <= self.max_dist)[0]
#                     if len(candidates) > 0:
#                         row[candidates[np.argmin(self.dist[i][candidates])]] = 1

#             # Garante que as capacidades dos ODCs não sejam ultrapassadas
#             load = np.dot(self.oru_cpu, X)
#             for j in range(X.shape[1]):
#                 while load[j] > self.odc_cap:
#                     overloaded_indices = np.where(X[:, j] == 1)[0]
#                     if len(overloaded_indices) == 0:
#                         break
#                     i = overloaded_indices[np.argmax(self.dist[overloaded_indices, j])]
#                     X[i, j] = 0
#                     load[j] -= self.oru_cpu[i]

#                     # Reatribuir esse ORU a outro ODC
#                     available = [k for k in range(X.shape[1]) if self.dist[i, k] <= self.max_dist and load[k] + self.oru_cpu[i] <= self.odc_cap]
#                     if available:
#                         new_j = available[np.argmin(self.dist[i, available])]
#                         X[i, new_j] = 1
#                         load[new_j] += self.oru_cpu[i]

#             individual.set("X", X.flatten())
#         return pop


class ODCRepair(Repair):
    def __init__(self, oru_cpu, odc_cap, max_dist, dist_matrix):
        super().__init__()
        self.oru_cpu = np.array(oru_cpu)
        self.odc_cap = odc_cap
        self.max_dist = max_dist
        self.dist = dist_matrix

    def _do(self, problem, X, **kwargs):
        n_orus = len(self.oru_cpu)
        n_odcs = self.dist.shape[1]

        for i in range(X.shape[0]):  # Para cada indivíduo
            x = X[i].reshape(n_orus, n_odcs)

            # Corrige múltiplas atribuições ou nenhuma
            for oru_idx, row in enumerate(x):
                if np.sum(row) != 1:
                    assigned = np.argmin(self.dist[oru_idx])  # escolha o mais próximo
                    row[:] = 0
                    row[assigned] = 1

            # Remove atribuições inválidas por distância
            for oru_idx in range(n_orus):
                for odc_idx in range(n_odcs):
                    if self.dist[oru_idx, odc_idx] > self.max_dist:
                        x[oru_idx, odc_idx] = 0

            # Garante uma alocação por ORU novamente
            for oru_idx, row in enumerate(x):
                if np.sum(row) == 0:
                    candidates = np.where(self.dist[oru_idx] <= self.max_dist)[0]
                    if len(candidates) > 0:
                        best = candidates[np.argmin(self.dist[oru_idx, candidates])]
                        row[best] = 1

            # Verifica a carga nos ODCs
            load = np.dot(self.oru_cpu, x)
            for odc_idx in range(n_odcs):
                while load[odc_idx] > self.odc_cap:
                    overloaded_orus = np.where(x[:, odc_idx] == 1)[0]
                    if len(overloaded_orus) == 0:
                        break
                    worst = overloaded_orus[np.argmax(self.dist[overloaded_orus, odc_idx])]
                    x[worst, odc_idx] = 0
                    load[odc_idx] -= self.oru_cpu[worst]

                    # Reatribui o ORU removido
                    available = [j for j in range(n_odcs)
                                 if self.dist[worst, j] <= self.max_dist and load[j] + self.oru_cpu[worst] <= self.odc_cap]
                    if available:
                        new_j = available[np.argmin(self.dist[worst, available])]
                        x[worst, new_j] = 1
                        load[new_j] += self.oru_cpu[worst]

            # Salva de volta no X
            X[i] = x.flatten()

        return X


class ODCProblem(ElementwiseProblem):
    def __init__(self, oru_cpu, odc_cap, dist_matrix, max_dist):
        self.n_orus = len(oru_cpu)
        self.n_odcs = dist_matrix.shape[1]
        self.oru_cpu = np.array(oru_cpu)
        self.odc_cap = odc_cap
        self.dist = dist_matrix
        self.max_dist = max_dist
        super().__init__(
            n_var=self.n_orus * self.n_odcs,
            n_obj=2,
            n_constr=0,
            xl=0,
            xu=1,
            type_var=np.bool_
        )

    def _evaluate(self, x, out, *args, **kwargs):
        x = x.reshape(self.n_orus, self.n_odcs)

        # Verifica atribuições inválidas
        valid = np.sum(x, axis=1) == 1
        if not np.all(valid):
            out["F"] = [1e6, 1e6]
            return

        # Verifica distâncias
        if np.any(x * self.dist > self.max_dist):
            out["F"] = [1e6, 1e6]
            return

        # Calcula carga por ODC
        odc_load = np.dot(self.oru_cpu, x)
        if np.any(odc_load > self.odc_cap):
            out["F"] = [1e6, 1e6]
            return

        # f1 = -np.sum(self.oru_cpu * x)  # Maximize CPUs
        f1 = -np.sum(self.oru_cpu[:, None] * x)
        f2 = np.sum(self.dist * x) / self.n_orus  # Minimize average distance

        out["F"] = [f1, f2]