# Standard imports
import numpy as np

# Tenta importar CuPy, e define um placeholder se não estiver disponível
try:
    import cupy as cp
    CUDA_AVAILABLE = True
    print("CuPy importado com sucesso. Usando GPU.")
except ImportError:
    cp = np # Fallback para NumPy se CuPy não estiver disponível
    CUDA_AVAILABLE = False
    print("CuPy não encontrado. Usando NumPy (CPU) como fallback.")

import pandas as pd
import matplotlib.pyplot as plt
import locale
import warnings
import math
from sklearn.exceptions import ConvergenceWarning
from sklearn.cluster import KMeans
import re
import time # Para medir o tempo
import os # Para criar diretórios

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
try:
    locale.setlocale(locale.LC_NUMERIC, 'C')
except locale.Error:
    print("Aviso: Não foi possível definir o locale para 'C'. Usando o locale padrão do sistema.")


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


class MOFLP(Problem): # Sua classe MOFLP, com otimizações de memória e CUDA
    def __init__(self, args, orus, odcs, distances_np): # distances_np é NumPy array da CPU
        self.orus_data = orus
        self.odcs_data = odcs # Agora é uma lista de dicts com 'id', 'lat', 'lon'
        self.args = args

        self.O = len(self.orus_data)
        self.C = len(self.odcs_data)

        if self.O == 0 or self.C == 0:
            raise ValueError("Número de ORUs ou ODCs não pode ser zero para MOFLP.")

        lambda_o_np_init = np.array([oru['cpu_cores'] for oru in self.orus_data], dtype=np.float32)
        
        current_max_capacity = self.args.max_capacity
        if isinstance(current_max_capacity, (list, np.ndarray)):
            if len(current_max_capacity) == self.C:
                mu_c_np_init = np.array(current_max_capacity, dtype=np.float32)
            elif len(current_max_capacity) == 1:
                 mu_c_np_init = np.full(self.C, current_max_capacity[0], dtype=np.float32)
            else:
                raise ValueError(f"args.max_capacity como lista/array (tamanho {len(current_max_capacity)}) deve ter tamanho C ({self.C}) ou 1.")
        else:
            mu_c_np_init = np.full(self.C, current_max_capacity, dtype=np.float32)

        self.D_max_val = float(args.max_distance)
        max_diff_dist = 0.0
        if distances_np.size > 0:
             max_diff_dist = np.max(distances_np - self.D_max_val) # distances_np já é float32
        self.M_val = float(max(1.0, max_diff_dist) + 1.0)

        self._cp = cp if CUDA_AVAILABLE else np
        
        if CUDA_AVAILABLE: print("Transferindo dados constantes para a GPU no __init__...")
        else: print("CUDA não disponível. Usando NumPy para dados (CPU).")

        self.lambda_o_dev = self._cp.asarray(lambda_o_np_init)
        self.mu_c_dev = self._cp.asarray(mu_c_np_init)
        self.distances_dev = self._cp.asarray(distances_np) # distances_np já é float32
        self.D_max_dev = self._cp.float32(self.D_max_val)
        self.M_dev = self._cp.float32(self.M_val)
        
        if CUDA_AVAILABLE: print("Dados constantes no dispositivo.")

        n_vars = 2 * self.O * self.C
        # xl, xu devem ser NumPy arrays para pymoo
        xl = np.zeros(n_vars, dtype=np.float32)
        xu = np.ones(n_vars, dtype=np.float32)
        n_obj = 2
        n_constr = (2 * self.O) + self.C + (2 * self.O * self.C)

        super().__init__(n_var=n_vars, n_obj=n_obj, n_constr=n_constr, xl=xl, xu=xu)

    def _evaluate(self, X_batch_np, out, *args, **kwargs):
        # X_batch_np é da CPU (NumPy), dtype=float32
        
        # Transferir X_batch para o dispositivo (GPU ou permanece como NumPy array)
        # Evitar re-transferência se já estiver no dispositivo correto (relevante se pymoo otimizar)
        if isinstance(X_batch_np, self._cp.ndarray):
            X_batch_dev = X_batch_np # Já está no dispositivo correto
        else:
            X_batch_dev = self._cp.asarray(X_batch_np, dtype=self._cp.float32)


        n_solutions = X_batch_dev.shape[0]

        x_flat_batch = X_batch_dev[:, :self.O * self.C]
        y_flat_batch = X_batch_dev[:, self.O * self.C:]

        # Para problemas binários, os operadores de pymoo (sampling, crossover, mutation)
        # devem idealmente fornecer valores que são 0.0 ou 1.0.
        # Se eles fornecerem valores fracionários, arredondar pode ser uma forma de forçar
        # a natureza binária, mas pode interferir na forma como o gradiente (implícito) é percebido.
        # A melhor abordagem é garantir que os operadores gerem binários.
        # BinaryRandomSampling, TwoPointCrossover, BitflipMutation devem fazer isso.
        # Se X_batch_dev ainda tiver floats não binários, pode ser devido a como pymoo
        # lida com 'var_type' internamente ou como os limites xl, xu (floats) são interpretados.
        # Por ora, vamos assumir que os valores são efetivamente binários.
        x_matrices = x_flat_batch.reshape((n_solutions, self.O, self.C))
        y_matrices = y_flat_batch.reshape((n_solutions, self.O, self.C))

        lambda_o_b = self.lambda_o_dev[self._cp.newaxis, :, self._cp.newaxis]
        distances_b = self.distances_dev[self._cp.newaxis, :, :]
        mu_c_b = self.mu_c_dev[self._cp.newaxis, :]

        f1_batch = -self._cp.sum(lambda_o_b * x_matrices, axis=(1, 2))
        f2_batch = self._cp.sum(distances_b * x_matrices, axis=(1, 2))
        F_batch_dev = self._cp.column_stack([f1_batch, f2_batch])

        G_batch_dev = self._cp.zeros((n_solutions, self.n_constr), dtype=self._cp.float32)
        idx = 0

        sum_x_over_c = self._cp.sum(x_matrices, axis=2)
        G_batch_dev[:, idx : idx+self.O] = sum_x_over_c - 1.0; idx += self.O
        G_batch_dev[:, idx : idx+self.O] = 1.0 - sum_x_over_c; idx += self.O
        
        sum_lambda_x_o = self._cp.sum(lambda_o_b * x_matrices, axis=1)
        G_batch_dev[:, idx:idx+self.C] = sum_lambda_x_o - mu_c_b; idx += self.C
        
        g_dist_aux1 = distances_b - self.D_max_dev - self.M_dev * y_matrices
        g_dist_aux2 = x_matrices + y_matrices - 1.0
        
        G_batch_dev[:, idx:idx+self.O*self.C] = g_dist_aux1.reshape(n_solutions, -1); idx += self.O*self.C
        G_batch_dev[:, idx:idx+self.O*self.C] = g_dist_aux2.reshape(n_solutions, -1)

        if CUDA_AVAILABLE:
            out["F"] = cp.asnumpy(F_batch_dev)
            out["G"] = cp.asnumpy(G_batch_dev)
        else:
            out["F"] = F_batch_dev
            out["G"] = G_batch_dev


def run_nsga2(args, orus, odcs, distances):
    problem = MOFLP(args, orus, odcs, distances)

    n_procs = args.no_processes 
    parallelization_setup = None
    pool = None 

    if n_procs > 1:
        if CUDA_AVAILABLE:
            print(f"Aviso: Multiprocessing ({n_procs} processos) com CUDA. Monitore contenção de GPU.")
        
        actual_n_procs = min(n_procs, multiprocessing.cpu_count())
        if actual_n_procs != n_procs:
            print(f"Ajustando no_processes de {n_procs} para {actual_n_procs}.")
        n_procs = actual_n_procs
            
        if n_procs > 0:
            try:
                # Tentar 'spawn' para melhor compatibilidade com CUDA em alguns sistemas
                # ctx = multiprocessing.get_context('spawn')
                # pool = ctx.Pool(processes=n_procs)
                pool = multiprocessing.Pool(processes=n_procs)
                parallelization_setup = StarmapParallelization(pool.starmap)
                print(f"Paralelização com multiprocessing: {n_procs} processos.")
            except Exception as e:
                print(f"Falha ao criar multiprocessing.Pool: {e}. Modo serial.")
                if pool: pool.close(); pool.join()
                pool = None; parallelization_setup = None
        else: print("Paralelização desabilitada (n_procs <= 0).")
    else: print(f"Modo serial (no_processes={n_procs}).")

    # Usar var_type=bool para BinaryRandomSampling se as variáveis são realmente binárias
    # e xl, xu são 0 e 1. Pymoo pode converter para float depois.
    # Se xl, xu são float32, então BinaryRandomSampling(var_type=np.float32) é consistente.
    algorithm = NSGA2(
        pop_size=args.population_size,
        sampling=BinaryRandomSampling(var_type=np.float32), # Amostrar como float32 se xl/xu são float32
        crossover=TwoPointCrossover(), 
        mutation=BitflipMutation(prob=(1.0 / problem.n_var if problem.n_var > 0 else 0.01)),
        eliminate_duplicates=True,
        parallelization=parallelization_setup 
    )

    termination = get_termination("n_gen", args.num_gen)

    print(f"Iniciando NSGA-II (CUDA Habilitado: {CUDA_AVAILABLE}). Pop: {args.population_size}, Gen: {args.num_gen}")
    start_time = time.time()
    result = minimize(
        problem=problem,
        algorithm=algorithm,
        termination=termination,
        seed=args.seed,
        verbose=True,
        save_history=False # <<< MUDANÇA CRÍTICA PARA MEMÓRIA RAM
    )
    end_time = time.time()
    print(f"Otimização concluída em {end_time - start_time:.2f} segundos.")

    if pool is not None:
        pool.close(); pool.join()
        print("Pool de processos (multiprocessing) fechado.")
        
    return result, problem

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