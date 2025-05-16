import random
import numpy as np
from src.base_optimizer import BaseOptimizer


class RandomOptimizer(BaseOptimizer):
    def run(self):
        num_odcs = len(self.problem.initial_odcs)
        best_score = float("inf")
        best_solution = None

        for _ in range(self.args.num_trials):
            solution = np.array([random.random() for _ in range(num_odcs)]).reshape(1, -1)

            # Chamada correta para obter os objetivos e restrições
            F, G = self.problem.evaluate(solution, return_values_of=["F", "G"])
            objectives = F[0]
            constraints = G[0]

            self.tracker.update(solution[0], objectives)

            score = sum(objectives)  # já ponderado

            if score < best_score:
                best_score = score
                best_solution = solution

        # Avaliação final da melhor solução
        F, G = self.problem.evaluate(best_solution, return_values_of=["F", "G"])
        print(f'\n========== Valor de F:{F} ============\n')
        print(f'\n========== Valor de G:{G} ============\n')
        final_objectives = F[0]
        final_constraints = G[0]

        # Salvar a melhor solução no tracker
        self.tracker.best_solutions.append(
            self.format_solution(
                solution=best_solution[0],
                objectives=final_objectives,
                constraints=final_constraints,
                name="Random"
            )
        )

        return self.tracker.best_solutions[-1]