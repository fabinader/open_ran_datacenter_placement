# Standard imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import locale
import warnings
import math
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import KMeans
import re

# pymoo imports
from pymoo.core.problem import Problem
# from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Binary
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.indicators.hv import Hypervolume

import multiprocessing
from pymoo.core.problem import StarmapParallelization

# Custom imports
from src.config import SimulationConfig

# Set locale to ensure dot-separated decimal representation
locale.setlocale(locale.LC_NUMERIC, 'C')


class Utils():
    @staticmethod
    def extract_bandwidth(designation):
        unit_dict = {
            'H': 1e-6,    # Hertz to Megahertz
            'K': 1e-3,    # Kilohertz to Megahertz
            'M': 1,       # Megahertz to Megahertz
            'G': 1e3      # Gigahertz to Megahertz
        }

        for i, char in enumerate(designation):
            if char in unit_dict:
                numeric_part = designation[:i]
                unit = char
                break

        bandwidth_mhz = float(numeric_part) * unit_dict[unit]
        return bandwidth_mhz

    @staticmethod
    def calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz):
        return (bandwidth_mhz / 100) * cpu_per_100mhz

    @staticmethod
    def read_orus(file_path, cpu_per_100mhz):
        df = pd.read_csv(file_path, converters={
            'latitude': locale.atof,
            'longitude': locale.atof
        })

        # Remove duplicadas com base em latitude e longitude
        df = df.drop_duplicates(subset=['latitude', 'longitude'])

        orus = []
        for index, row in df.iterrows():
            bandwidth_mhz = Utils.extract_bandwidth(row['emission_designation'])
            cpu_cores = Utils.calculate_cpu_cores(bandwidth_mhz, cpu_per_100mhz)
            oru = {
                "cell_site_id": row['cell_site_id'],
                "emission_designation": row['emission_designation'],
                "technology": row['technology'],
                "tx_frequency": row['tx_frequency'],
                "rx_frequency": row['rx_frequency'],
                "azimuth": row['azimuth'],
                "antenna_gain": row['antenna_gain'],
                "back_front_relation": row['back_front_relation'],
                "hpa": row['hpa'],
                "mechanical_elevation": row['mechanical_elevation'],
                "polarization": row['polarization'],
                "antenna_height": row['antenna_height'],
                "tx_power": row['tx_power'],
                "latitude": row['latitude'],
                "longitude": row['longitude'],
                "cell_carrier_id": row['cell_carrier_id'],
                "bandwidth_mhz": bandwidth_mhz,
                "cpu_cores": math.ceil(cpu_cores),
                "oru_id": len(orus) + 1  # Garante IDs únicos e sequenciais após filtro
            }
            orus.append(oru)

        return orus

    @staticmethod
    def generate_odcs(orus, num_odcs, seed):
        if num_odcs == 0:
            num_odcs = len(orus)  # ODCs = O-RUs

        distinct_clusters = 0
        n_clusters = 0
        lat_lon = np.array([[c["latitude"], c["longitude"]] for c in orus])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ConvergenceWarning)
            kmeans = KMeans(n_clusters=num_odcs, random_state=seed).fit(lat_lon)
            odcs = kmeans.cluster_centers_

            # Check if a ConvergenceWarning was raised
            if w and issubclass(w[-1].category, ConvergenceWarning):
                warning_message = str(w[-1].message)
                print("ConvergenceWarning was raised")
                print(warning_message)

                # Extract numbers from the warning message using regex
                numbers = re.findall(r'\d+', warning_message)

                if len(numbers) >= 2:
                    distinct_clusters = int(numbers[0])
                    n_clusters = int(numbers[1])
                    print(f"Number of distinct clusters: {distinct_clusters}")
                    print(f"n_clusters: {n_clusters}")
                    kmeans = KMeans(n_clusters=distinct_clusters, random_state=seed).fit(lat_lon)
                    odcs = kmeans.cluster_centers_
                else:
                    print("Could not extract the required numbers from the warning message.")
            else:
                print("No ConvergenceWarning")

        return [(lat, lon) for lat, lon in odcs]

    @staticmethod
    def haversine_np(lat1, lon1, lat2, lon2):
        R = 6371.0  # Earth radius in kilometers
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c

    @staticmethod
    def precompute_distances(orus, odcs):
        orus_coords = np.array([(oru["latitude"], oru["longitude"]) for oru in orus])
        odc_coords = np.array(odcs)
        num_orus = len(orus)
        num_odcs = len(odcs)

        distances = np.zeros((num_orus, num_odcs))
        for i in range(num_orus):
            distances[i, :] = Utils.haversine_np(
                np.full(num_odcs, orus_coords[i, 0]),
                np.full(num_odcs, orus_coords[i, 1]),
                odc_coords[:, 0],
                odc_coords[:, 1]
            )

        return distances


class MOFLP(Problem):
    def __init__(self, args, orus, odcs, distances):
        """
        :param orus: Lista de O-RUs (dicionários com informações, incluindo 'cpu_cores').
        :param odcs: Lista de ODCs (usado para determinar self.C).
        :param distances: Matriz de distâncias pré-computadas [O x C] (NumPy array).
        :param args: Objeto de configuração, contendo:
                     args.max_capacity: Capacidade de processamento de cada ODC (vCPU).
                                        Pode ser um escalar ou um array [C].
                     args.max_distance: Distância máxima permitida (km).
        """
        self.orus = orus
        self.odcs = odcs
        self.distances = distances  # Matriz O x C
        self.args = args

        # Parâmetros do problema
        self.O = len(orus)
        self.C = len(odcs)

        if self.O == 0 or self.C == 0:
            raise ValueError("Número de ORUs ou ODCs não pode ser zero.")

        self.lambda_o = np.array([oru['cpu_cores'] for oru in orus])  # Vetor O

        if isinstance(self.args.max_capacity, (list, np.ndarray)):
            if len(self.args.max_capacity) == self.C:
                self.mu_c = np.array(self.args.max_capacity)  # Vetor C
            else:
                raise ValueError("args.max_capacity deve ser um escalar ou uma lista/array com tamanho C.")
        else:
            self.mu_c = np.full(self.C, self.args.max_capacity)  # Vetor C

        self.D_max = args.max_distance

        # Cálculo do Big-M
        # M deve ser suficientemente grande para que M * y_o,c não restrinja
        # d_o,c - D_max quando y_o,c = 1.
        # M >= d_o,c - D_max. Uma escolha segura é M > max(d_o,c - D_max).
        # Se todas as d_o,c - D_max forem negativas, qualquer M > 0 funciona.
        # Para garantir que M seja positivo e suficientemente grande:
        max_diff_dist = np.max(self.distances - self.D_max)
        self.M = max(1.0, max_diff_dist) + 1.0 # Garante que M seja positivo e maior que a diferença máxima
                                                # Adicionar 1.0 para folga.
        # Uma alternativa mais simples e frequentemente usada para M é max(d_o,c) se D_max >= 0
        # self.M = np.max(self.distances) + 1.0 # Se D_max for muito grande, d-D_max pode ser muito negativo.

        # Número de variáveis de decisão:
        # O*C variáveis x_o,c (binárias)
        # O*C variáveis y_o,c (binárias)
        # Total: 2 * O * C
        n_vars = 2 * self.O * self.C

        # Limites das variáveis (0 ou 1 para binárias)
        # xl será um vetor de zeros, xu um vetor de uns.
        xl = np.zeros(n_vars)
        xu = np.ones(n_vars)

        # Número de objetivos
        n_obj = 2

        # Número de restrições (todas g_i(X) <= 0):
        # 1. Atribuição O-RU: sum_c(x_o,c) = 1  => 2 * O restrições
        #    sum_c(x_o,c) - 1 <= 0
        #    1 - sum_c(x_o,c) <= 0
        # 2. Capacidade ODC: sum_o(lambda_o * x_o,c) - mu_c <= 0 => C restrições
        # 3. Distância Auxiliar 1 (Big-M): d_o,c - D_max - M*y_o,c <= 0 => O*C restrições
        # 4. Distância Auxiliar 2 (Big-M): x_o,c + y_o,c - 1 <= 0 => O*C restrições
        n_constr = (2 * self.O) + self.C + (2 * self.O * self.C)

        super().__init__(n_var=n_vars,
                         n_obj=n_obj,
                         n_constr=n_constr,
                         xl=xl,
                         xu=xu)

    def _evaluate(self, X_batch, out, *args, **kwargs):
        # X_batch é uma matriz (n_solutions, n_vars)
        n_solutions = X_batch.shape[0]

        # --- Desempacotar e Remodelar Variáveis ---
        # As primeiras O*C colunas são x_o,c, as próximas O*C são y_o,c.
        x_flat_batch = X_batch[:, :self.O * self.C]
        y_flat_batch = X_batch[:, self.O * self.C:]

        # Remodelar para (n_solutions, O, C)
        x_matrices = x_flat_batch.reshape((n_solutions, self.O, self.C))
        y_matrices = y_flat_batch.reshape((n_solutions, self.O, self.C))

        # --- Cálculo dos Objetivos (vetorizado) ---
        # lambda_o: (O,) -> (1, O, 1) para broadcasting
        # distances: (O, C) -> (1, O, C) para broadcasting

        f1_batch = -np.sum(self.lambda_o[np.newaxis, :, np.newaxis] * x_matrices, axis=(1, 2))
        f2_batch = np.sum(self.distances[np.newaxis, :, :] * x_matrices, axis=(1, 2))

        out["F"] = np.column_stack([f1_batch, f2_batch])

        # --- Cálculo das Restrições (vetorizado) ---
        # Inicializar a matriz G para todas as restrições
        G_batch = np.zeros((n_solutions, self.n_constr)) # self.n_constr é o total

        # Ponteiro para a coluna atual em G_batch
        current_constr_idx = 0

        # Restrição 1: Atribuição O-RU: sum_c(x_o,c) = 1 (para cada o)
        # x_matrices tem shape (n_sols, O, C)
        sum_x_over_c = np.sum(x_matrices, axis=2) # Shape: (n_sols, O)
        
        g_assign1 = sum_x_over_c - 1
        g_assign2 = 1 - sum_x_over_c
        
        G_batch[:, current_constr_idx : current_constr_idx + self.O] = g_assign1
        current_constr_idx += self.O
        G_batch[:, current_constr_idx : current_constr_idx + self.O] = g_assign2
        current_constr_idx += self.O

        # Restrição 2: Capacidade ODC: sum_o(lambda_o * x_o,c) <= mu_c (para cada c)
        # lambda_o: (O,) -> (1, O, 1)
        # mu_c: (C,) -> (1, C)
        sum_lambda_x_over_o = np.sum(self.lambda_o[np.newaxis, :, np.newaxis] * x_matrices, axis=1) # Shape: (n_sols, C)
        g_capacity = sum_lambda_x_over_o - self.mu_c[np.newaxis, :] # Broadcasting mu_c
        
        G_batch[:, current_constr_idx : current_constr_idx + self.C] = g_capacity
        current_constr_idx += self.C
        
        # Restrições Big-M para distância:
        # d_o,c - D_max - M*y_o,c <= 0
        # distances: (O,C) -> (1,O,C)
        # y_matrices: (n_sols,O,C)
        g_dist_aux1 = self.distances[np.newaxis, :, :] - self.D_max - self.M * y_matrices
        # x_o,c + y_o,c - 1 <= 0
        g_dist_aux2 = x_matrices + y_matrices - 1
        
        # Achatar as restrições de distância para preencher G_batch
        # Cada uma tem O*C restrições por solução
        G_batch[:, current_constr_idx : current_constr_idx + (self.O * self.C)] = g_dist_aux1.reshape(n_solutions, -1)
        current_constr_idx += (self.O * self.C)
        G_batch[:, current_constr_idx : current_constr_idx + (self.O * self.C)] = g_dist_aux2.reshape(n_solutions, -1)
        current_constr_idx += (self.O * self.C) # Garante que o índice está correto no final

        out["G"] = G_batch


def run_nsga2(args, orus, odcs, distances):
    # Create a problem instance
    problem = MOFLP(args, orus, odcs, distances)

    # --- Configuração da Paralelização ---
    # Define o número de processos a serem usados.
    # args.no_processes deve ser definido na sua configuração.
    # É importante não definir mais processos do que os núcleos disponíveis na CPU.
    n_procs = args.no_processes
    if n_procs > multiprocessing.cpu_count():
        print(f"Aviso: args.no_processes ({n_procs}) excede o número de CPUs ({multiprocessing.cpu_count()}). Ajustando para {multiprocessing.cpu_count()}.")
        n_procs = multiprocessing.cpu_count()
    if n_procs <= 0:  # Caso no_processes não seja positivo
        print(f"Aviso: args.no_processes ({n_procs}) é inválido. Usando 1 processo (sem paralelização explícita).")
        pool = None
        parallelization_setup = None
    else:
        pool = multiprocessing.Pool(processes=n_procs)
        parallelization_setup = StarmapParallelization(pool.starmap)
        print(f"Paralelização configurada com {n_procs} processos.")

    algorithm = NSGA2(
        pop_size=args.population_size,
        sampling=BinaryRandomSampling(),
        crossover=TwoPointCrossover(),
        mutation=BitflipMutation(prob=(1.0 / problem.n_var if problem.n_var > 0 else 0.01)),
        eliminate_duplicates=True,
        parallelization=parallelization_setup  # Passa o setup de paralelização
    )

    # Defines stopping criteria
    termination = get_termination("n_gen", args.num_gen)

    # Executes the optimization
    result = minimize(
        problem=problem,
        algorithm=algorithm,
        termination=termination,
        seed=args.seed,
        verbose=True,
        save_history=True
    )

    return result

def analyze_results(result, orus, odcs, distances, args):
    # Analyzing results
    if result.X is None or len(result.X) == 0:
        print("No solution found on Pareto frontier.")
        return []

    # Pareto Front
    F = result.F

    # --- Plotar fronteira de Pareto ---
    plt.figure(figsize=(10, 6))
    plt.scatter(-F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue', label='Pareto solutions')
    plt.title("Pareto Front - MO-FLP for Open RAN")
    plt.xlabel("Total Allocated Capacity (vCPU)")
    plt.ylabel("Total Fronthaul Distance (km)")
    plt.grid(True)
    plt.legend()

    # Salvar figura
    plt.savefig(f"{args.output_dir}/pareto_front.png")
    plt.close()

    # --- Plotar Hipervolume ---
    # print("Valores mínimos e máximos de cada objetivo:")
    # print(f"f1: min = {np.min(result.F[:, 0]):.6f}, max = {np.max(result.F[:, 0]):.6f}")
    # print(f"f2: min = {np.min(result.F[:, 1]):.6f}, max = {np.max(result.F[:, 1]):.6f}")

    # # Cálculo do Hipervolume
    # ref_point = np.array([285000, 132000.0])
    # indicator_hv = Hypervolume(ref_point=ref_point)
    # hv = indicator_hv.do(result.F)
    # print(f"Hipervolume final: {hv:.4f}")

    # # Evolução do Hipervolume
    # hv_history = []
    # for entry in result.history:
    #     F = entry.pop.get("F")
    #     hv_history.append(indicator_hv.do(F))

    # plt.figure(figsize=(8, 5))
    # plt.plot(hv_history, marker='o', linestyle='-', color='green')
    # plt.title("Convergência do Hipervolume")
    # plt.xlabel("Geração")
    # plt.ylabel("Hipervolume")
    # plt.grid(True)
    # plt.show()

    if F.shape[0] > 0:  # Verifica se há soluções para calcular o hipervolume
        print("\nValores mínimos e máximos de cada objetivo na fronteira de Pareto:")
        # Lembre-se que F[:,0] é -capacidade
        print(f"Capacidade Alocada (Objetivo 1 maximizado): min = {np.min(-F[:, 0]):.2f}, max = {np.max(-F[:, 0]):.2f}")
        print(f"Distância Total (Objetivo 2 minimizado): min = {np.min(F[:, 1]):.2f}, max = {np.max(F[:, 1]):.2f}")

        # Ponto de referência para o Hipervolume
        # Deve ser pior que qualquer ponto na fronteira de Pareto
        # Para f1 (-capacidade), um valor mais negativo é pior.
        # Para f2 (distância), um valor maior é pior.
        ref_point_f1 = np.min(F[:, 0]) - abs(np.min(F[:, 0]) * 0.1) - 1  # Pior que a pior capacidade (mais negativo)
        ref_point_f2 = np.max(F[:, 1]) + abs(np.max(F[:, 1]) * 0.1) + 1  # Pior que a pior distância
        ref_point = np.array([ref_point_f1, ref_point_f2])
        
        print(f"Ponto de referência para Hipervolume: {ref_point}")

        indicator_hv = Hypervolume(ref_point=ref_point)
        hv = indicator_hv.do(F)  # F já está no formato que o pymoo espera (minimização)
        print(f"Hipervolume final: {hv:.4f}")

        # Evolução do Hipervolume (se o histórico foi salvo)
        if result.history is not None and len(result.history) > 0:
            hv_history = []
            for generation_data in result.history:
                # Em versões mais recentes do pymoo, 'pop' pode não estar diretamente no history.
                # 'opt' contém a fronteira de Pareto daquela geração.
                if generation_data.opt is not None and len(generation_data.opt) > 0:
                    F_gen = generation_data.opt.get("F")
                    if F_gen is not None and F_gen.shape[0] > 0:
                        # Garante que F_gen tenha pelo menos uma solução e 2 objetivos
                        if F_gen.ndim == 2 and F_gen.shape[1] == 2:
                            hv_history.append(indicator_hv.do(F_gen))
                        else:
                             hv_history.append(0)  # Ou algum valor indicando problema
                    else:
                        hv_history.append(0)  # Sem soluções na fronteira para esta geração
                else:
                     hv_history.append(0)  # Sem população ótima registrada

            plt.figure(figsize=(8, 5))
            plt.plot(range(1, len(hv_history) + 1), hv_history, marker='o', linestyle='-', color='green')
            plt.title("Hipervolume Convergence")
            plt.xlabel("Generation")
            plt.ylabel("Hipervolume")
            plt.grid(True)
            output_path_hv = f"{args.output_dir}/hypervolume_convergence.png"
            plt.savefig(output_path_hv)
            print(f"Hipervolume convergence saved in: {output_path_hv}")
        else:
            print("Histórico não disponível para plotar a evolução do hipervolume.")
    else:
        print("Nenhuma solução na fronteira de Pareto para calcular o hipervolume.")

    # --- Salvar resultados em CSV ---

    # solutions = []
    # for i, x in enumerate(result.X):
    #     x_matrix = x.reshape((len(orus), len(odcs)))
    #     capacity = -result.F[i, 0]
    #     total_distance = result.F[i, 1]

    #     # Mapear alocações
    #     allocations = []
    #     for o in range(len(orus)):
    #         c = np.where(x_matrix[o,:] == 1)[0][0]
    #         allocations.append({
    #             "ORU_ID": orus[o]['oru_id'],
    #             "ODC_ID": c,
    #             "Distance_km": distances[o,c],
    #             "CPU_Cores": orus[o]['cpu_cores']
    #         })

    #     solutions.append({
    #         "Solution_ID": i,
    #         "Total_Capacity": capacity,
    #         "Total_Distance": total_distance,
    #         "Allocations": allocations
    #     })

    # # Converter para DataFrame e salvar
    # df_solutions = pd.DataFrame([{
    #     "Solution_ID": sol["Solution_ID"],
    #     "Total_Capacity": sol["Total_Capacity"],
    #     "Total_Distance": sol["Total_Distance"]
    # } for sol in solutions])

    # df_allocations = pd.DataFrame([
    #     {
    #         "Solution_ID": sol["Solution_ID"],
    #         "ORU_ID": alloc["ORU_ID"],
    #         "ODC_ID": alloc["ODC_ID"],
    #         "Distance_km": alloc["Distance_km"],
    #         "CPU_Cores": alloc["CPU_Cores"]
    #     }
    #     for sol in solutions
    #     for alloc in sol["Allocations"]
    # ])

    # df_solutions.to_csv(f"{args.output_dir}/solutions_summary.csv", index=False)
    # df_allocations.to_csv(f"{args.output_dir}/allocations_detail.csv", index=False)

    # return solutions

    O = len(orus)
    C = len(odcs)
    solutions_data = []

    for i, x_solution_vector in enumerate(result.X):
        # Extrai apenas as variáveis x_o,c (as primeiras O*C)
        x_flat = x_solution_vector[:O * C]
        x_matrix = x_flat.reshape((O, C)).astype(int)  # Converte para int para facilitar a verificação

        capacity = -result.F[i, 0]  # Capacidade real (positiva)
        total_distance = result.F[i, 1]

        # Mapear alocações
        current_solution_allocations = []
        for o_idx in range(O):
            # Encontra a ODC à qual a O-RU o_idx foi alocada
            # Deve haver exatamente uma alocação devido às restrições
            try:
                # np.where retorna uma tupla, pegamos o primeiro array, e o primeiro elemento dele
                c_idx = np.where(x_matrix[o_idx, :] == 1)[0][0]
                current_solution_allocations.append({
                    "ORU_ID": orus[o_idx].get('id', f'oru_{o_idx}'),  # Usar .get para segurança
                    "ODC_ID": odcs[c_idx].get('id', f'odc_{c_idx}'),  # Usar .get para segurança
                    "Distance_km": distances[o_idx, c_idx],
                    "CPU_Cores": orus[o_idx]['cpu_cores']
                })
            except IndexError:
                # Isso não deveria acontecer se as restrições de alocação forem satisfeitas
                print(f"AVISO: ORU {orus[o_idx].get('id', o_idx)} não foi alocada a nenhuma ODC na solução {i} ou alocada a múltiplas.")
                print(f"Linha da matriz x para ORU {o_idx}: {x_matrix[o_idx, :]}")


        solutions_data.append({
            "Solution_ID": i,
            "Total_Capacity": capacity,
            "Total_Distance": total_distance,
            "Allocations_Detail": current_solution_allocations # Lista de dicionários
        })

    # Converter para DataFrame e salvar
    if solutions_data:  # Verifica se há dados para salvar
        df_solutions_summary = pd.DataFrame([{
            "Solution_ID": sol["Solution_ID"],
            "Total_Capacity": sol["Total_Capacity"],
            "Total_Distance": sol["Total_Distance"]
        } for sol in solutions_data])

        # Para allocations_detail, precisamos "achatar" a lista
        df_allocations_list = []
        for sol in solutions_data:
            for alloc_detail in sol["Allocations_Detail"]:
                df_allocations_list.append({
                    "Solution_ID": sol["Solution_ID"],
                    "ORU_ID": alloc_detail["ORU_ID"],
                    "ODC_ID": alloc_detail["ODC_ID"],
                    "Distance_km": alloc_detail["Distance_km"],
                    "CPU_Cores": alloc_detail["CPU_Cores"]
                })
        df_allocations_detail = pd.DataFrame(df_allocations_list)

        output_path_summary = f"{args.output_dir}/solutions_summary.csv"
        output_path_detail = f"{args.output_dir}/allocations_detail.csv"
        
        df_solutions_summary.to_csv(output_path_summary, index=False)
        df_allocations_detail.to_csv(output_path_detail, index=False)
        print(f"Resumo das soluções salvo em: {output_path_summary}")
        print(f"Detalhes das alocações salvos em: {output_path_detail}")
    else:
        print("Nenhum dado de solução para salvar em CSV.")

    return solutions_data # Retorna os dados processados

def is_the_problem_feasible(args, orus, odcs, distances):
    # print(f'Demanda total de processamento: {np.sum(oru["cpu_cores"] for oru in orus)}')
    # print(f'Capacidade total de processamento: {args.max_capacity*args.num_odcs}')

    # for o, oru in enumerate(distances):
        # print(f'Distância média da O-RU {o} às ODCs: {np.mean(oru)}')

    # print(f'Distância média de cada O-RU às ODCs: {np.mean(distances, axis=1)}')

    print("\n--- Diagnóstico de Distâncias e Capacidades ---")

    O = len(orus)
    C = len(odcs)
    D_max = args.max_distance
    mu_c_scalar = args.max_capacity # Assumindo que é escalar por enquanto
    lambda_o_np = np.array([oru['cpu_cores'] for oru in orus])

    num_orus_sem_odc_proxima = 0
    for o_idx in range(O):
        distancias_para_esta_oru = distances[o_idx, :]
        odcs_alcancaveis = np.sum(distancias_para_esta_oru <= D_max)
        if odcs_alcancaveis == 0:
            num_orus_sem_odc_proxima += 1
            # print(f"ORU {orus[o_idx].get('id', o_idx)} não alcança nenhuma ODC. Dist min: {np.min(distancias_para_esta_oru)}")

    print(f"Número de O-RUs: {O}")
    print(f"Número de ODCs: {C}")
    print(f"Distância Máxima Permitida (D_max): {D_max} km")
    print(f"Número de O-RUs que NÃO conseguem alcançar NENHUMA ODC dentro de D_max: {num_orus_sem_odc_proxima} (de {O})")

    if O > 0 and num_orus_sem_odc_proxima == O:
        print("ALERTA CRÍTICO: NENHUMA O-RU consegue alcançar qualquer ODC com a D_max atual. O problema é inviável.")
    elif num_orus_sem_odc_proxima > 0:
        print(f"ALERTA: {num_orus_sem_odc_proxima} O-RUs podem ter dificuldade em serem alocadas devido à distância.")

    capacidade_total_odcs = C * mu_c_scalar
    demanda_total_orus = np.sum(lambda_o_np)
    print(f"Capacidade Total das ODCs: {capacidade_total_odcs} vCPU")
    print(f"Demanda Total das O-RUs: {demanda_total_orus} vCPU")

    if demanda_total_orus > capacidade_total_odcs:
        print(f"ALERTA: Demanda total das O-RUs ({demanda_total_orus}) excede a capacidade total das ODCs ({capacidade_total_odcs}).")
    print("---------------------------------------------\n")

def main():
    # 1. Load Configurations
    args = SimulationConfig()

    # 2. Load Data
    orus = Utils.read_orus(args.dataset, args.cpu_per_100mhz)

    # 3. Generate ODCs
    odcs = Utils.generate_odcs(orus, args.num_odcs, args.seed)

    # 4. Distance precomputation
    distances = Utils.precompute_distances(orus, odcs)

    # 5. Is the problem feasible
    # is_the_problem_feasible(args, orus, odcs, distances)

    # 6. Run NSGA-II optimization
    result = run_nsga2(args, orus, odcs, distances)

    # 7. Analyze results
    # analyze_results(result, orus, odcs, distances, args)

if __name__ == "__main__":
    main()