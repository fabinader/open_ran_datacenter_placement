import matplotlib.pyplot as plt


# def plot_pareto_front(objectives, label=None, save_path=None):
#     f1 = [obj[0] for obj in objectives]  # Ex: número de ODCs
#     f2 = [obj[1] for obj in objectives]  # Ex: distância média

#     plt.figure(figsize=(8, 6))
#     plt.scatter(f1, f2, c='blue', label=label or "Soluções Pareto", alpha=0.7)
#     plt.xlabel("Número de ODCs (f1)")
#     plt.ylabel("Distância Média (f2)")
#     plt.title("Fronteira de Pareto - NSGA-II")
#     plt.grid(True)
#     if label:
#         plt.legend()
#     if save_path:
#         plt.savefig(save_path)
#     else:
#         plt.show()

def plot_pareto_front(F, label=None, save_path=None):
    if F.shape[1] != 2:
        raise ValueError("Plot apenas para dois objetivos.")
    
    plt.figure(figsize=(8, 6))
    plt.scatter(F[:, 0], F[:, 1], c='blue', label=label or "Pareto Front")
    plt.xlabel("Objetivo 1")
    plt.ylabel("Objetivo 2")
    plt.title("Fronteira de Pareto")
    if label:
        plt.legend()
    if save_path:
        plt.savefig(save_path)
    plt.grid(True)
    plt.show()