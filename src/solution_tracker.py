import numpy as np


# class BestSolutionTracker:
#     def __init__(self, obj_weights):
#         self.obj_weights = obj_weights
#         self.best_solutions = []
#         self.best_objectives = []
#         self.best_idx = 0

#     # Usado por algoritmos populacionais como NSGA-II
#     def update_from_population(self, algorithm):
#         try:
#             composite_scores = (
#                 algorithm.pop.get("F")[:, 0] * self.obj_weights[0] +
#                 algorithm.pop.get("F")[:, 1] * self.obj_weights[1] +
#                 algorithm.pop.get("F")[:, 2] * self.obj_weights[2]
#             )
#             self.best_idx = np.argmin(composite_scores)
#             best_solution = algorithm.pop.get("X")[self.best_idx]
#             best_objective = algorithm.pop.get("F")[self.best_idx]
#             self.best_solutions.append(best_solution)
#             self.best_objectives.append(best_objective)
#         except Exception as e:
#             print(f"Error in BestSolutionTracker (population): {e}")

#     # Usado por heurísticas simples como Random, Greedy, etc.
#     def update(self, solution, objectives):
#         self.best_solutions.append(solution)
#         self.best_objectives.append(objectives)

#     def validation(self, num_trials):
#         if len(self.best_solutions) != num_trials:
#             print(f"Warning: Expected {num_trials} solutions, but found {len(self.best_solutions)}")

#         if not self.best_solutions:
#             print("No best solutions were found during the optimization process.")
        
#         print(f"Total generations with best solutions: {len(self.best_solutions)}")

class BestSolutionTracker:
    def __init__(self):
        self.best_solutions = []
        self.best_objectives = []
        self.best_idx = 0

    # Usado por algoritmos populacionais como NSGA-II
    def update_from_population(self, algorithm):
        try:
            # Apenas guarda todos os indivíduos não dominados da geração atual
            solutions = algorithm.pop.get("X")
            objectives = algorithm.pop.get("F")

            self.best_solutions.extend(solutions)
            self.best_objectives.extend(objectives)
        except Exception as e:
            print(f"Error in BestSolutionTracker (population): {e}")

    # Usado por heurísticas simples como Random, Greedy, etc.
    def update(self, solution, objectives):
        self.best_solutions.append(solution)
        self.best_objectives.append(objectives)

    def validation(self, num_trials):
        if not self.best_solutions:
            print("No best solutions were found during the optimization process.")
        else:
            print(f"Total solutions tracked: {len(self.best_solutions)}")