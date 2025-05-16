import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ConvergencePlot:
    @staticmethod
    def plot(result):
        history = result["plot"].history
        generations = len(history)
        avg_obj = np.zeros(generations)
        for i in range(generations):
            avg_obj[i] = history[i].pop.get("F").mean()

        fig,ax_con=plt.subplots(figsize=(8, 8))
        ax_con.plot(range(generations),avg_obj,marker='o')
        ax_con.set_xlabel("Generations")
        ax_con.set_ylabel("Average Objective Value")
        # ax_con.title("Convergence Plot")
        ax_con.grid(True)
        plt.tight_layout()
        plt.savefig("./output/nsga2/Convergence_plot.png", dpi=300)  # Save the figure as PNG
        plt.close()

        # Generate array2 as a range of integers from 0 to len(array1)-1
        x_array = list(range(generations))

        # Create a dictionary from the arrays
        data = {
            'generations': x_array,
            'avg_obj': avg_obj
        }

        # Create a DataFrame
        dfConvergence = pd.DataFrame(data)
        dfConvergence.to_csv("./output/nsga2/dfConvergence.csv", index=False)