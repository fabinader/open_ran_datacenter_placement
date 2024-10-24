import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path


path="/home/mbpaiva/Repositories/AUTORAN/ManausCase3"
jobs = 100
analysis= '4paper'

def listar_pastas(diretorio):
    caminho = Path(diretorio)
    for item in caminho.rglob("*"):  # Percorre recursivamente
        if item.is_dir():
            print(f"Pasta: {item}")
        # else:
        #     print(f"Arquivo: {item}")

# Exemplo de uso
listar_pastas(path)
