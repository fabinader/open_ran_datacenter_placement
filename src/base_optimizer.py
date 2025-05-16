from abc import ABC, abstractmethod


class BaseOptimizer(ABC):
    def __init__(self, problem, tracker, args):
        self.problem = problem
        self.tracker = tracker
        self.args = args

    @abstractmethod
    def run(self):
        """
        Runs the optimization process and returns the best solution found.
        """
        pass

    def format_solution(self, solution, objectives=None, constraints=None, name=None, plot=None):
        return {
            "solution": solution,
            "objectives": objectives,
            "constraints": constraints,
            "name": name if name else self.__class__.__name__,
            "plot": plot
        }