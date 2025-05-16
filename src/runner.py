from src.solution_tracker import BestSolutionTracker
from src.timer import Timer


# def run_all_heuristics(heuristics, problem, args):
#     """
#     Executa todos os otimizadores especificados no dicionário `heuristics`.

#     Args:
#         heuristics (dict): Mapeamento {nome: classe_do_otimizador}.
#         problem: Instância do problema a ser resolvido.
#         args: Argumentos de configuração (ex: num_trials, pesos, etc).

#     Returns:
#         dict: Resultados contendo a melhor solução, tracker e tempo por heurística.
#     """
#     results = {}
#     for name, OptimizerClass in heuristics.items():
#         print(f"\n===== Executing {name} Optimizer =====")
#         tracker = BestSolutionTracker()
#         optimizer = OptimizerClass(problem, tracker, args)
#         try:
#             with Timer(name=f"{name} Optimization") as t:
#                 result = optimizer.run()
#             results[name] = {
#                 "result": result,
#                 "tracker": tracker,
#                 "time": t.elapsed
#             }
#         except Exception as e:
#             print(f"❌ Error running {name}: {e}")
#             results[name] = {
#                 "result": None,
#                 "tracker": tracker,
#                 "time": None,
#                 "error": str(e)
#             }
#     return results

# src/runner.py

def run_all_heuristics(heuristics, problem, args):
    results = {}
    for name, OptimizerClass in heuristics.items():
        print(f"\n===== Executing {name} Optimizer =====")
        optimizer = OptimizerClass(problem, None, args)  # remove o tracker
        try:
            with Timer(name=f"{name} Optimization") as t:
                result = optimizer.run()
            results[name] = {
                "result": result,
                "time": t.elapsed
            }
        except Exception as e:
            print(f"❌ Error running {name}: {e}")
            results[name] = {
                "result": None,
                "time": None,
                "error": str(e)
            }
    return results