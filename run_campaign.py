import numpy as np
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Args Base
BASE_ARGS = ["-j", "100", "-c", "14", "-d", "11", "-C", "1000", "-o", "0", "-n"]

# Simulation Environments
SIM_DICT = [
    {'prob': 3, 'granu': 8, 'city': 'Manaus'},
    {'prob': 4, 'granu': 8, 'city': 'Manaus'},
    {'prob': 3, 'granu': 8, 'city': 'Natal'},
    {'prob': 4, 'granu': 8, 'city': 'Natal'}
]

# Shell Script Path (Verifique se este caminho é correto e acessível)
SHELL_PATH = '/home/mbpaiva/Repositories/AUTORAN/open_ran_datacenter_placement/campaign.sh'

def parser_string(w0, w1, w2, city, prob):
    weights = f"{w0:.1f},{w1:.1f},{w2:.1f}"
    campaign_name = f"{city}Case{prob}_{weights}"
    args = BASE_ARGS + [campaign_name, "-w", weights, '-y', city]
    return args

def exec_loop(w0,w1,w2,city,prob,shell_path):
  for i in range(len(w0)):
    args = parser_string(w0[i],w1[i],w2[i],city,prob)
    result = subprocess.run([shell_path] + args, capture_output=True, text=True)

def run_campaign(prob, granu, city, shell_path):
    if prob == 3:
        w0 = np.zeros(granu)
        w1 = np.linspace(0.1, 0.9, granu)
        w2 = 1 - w1
        exec_loop(w0, w1, w2, city, prob, shell_path)

    elif prob == 4:
        w0 = [0.1]*8 + [0.3]*5 + [0.5]*4 + [0.7]*2 + [0.8]
        w1 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.1, 0.2, 0.3, 0.5, 0.6, 0.1, 0.2, 0.3, 0.4, 0.1, 0.2, 0.1]
        w2 = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.6, 0.5, 0.4, 0.2, 0.1, 0.4, 0.3, 0.2, 0.1, 0.2, 0.1, 0.1]
        exec_loop(w0, w1, w2, city, prob, shell_path)

def main():
    for sim in SIM_DICT:
        run_campaign(sim['prob'], sim['granu'], sim['city'], SHELL_PATH)

# Correção: if __name__ == '__main__'
if __name__ == '__main__':
    main()
