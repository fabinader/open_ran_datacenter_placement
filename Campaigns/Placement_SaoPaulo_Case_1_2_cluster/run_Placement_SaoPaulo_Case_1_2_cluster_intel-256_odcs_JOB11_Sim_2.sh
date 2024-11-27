#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Case_1_2_cluster_odcs/JOB11/Sim_2
cp -f run_Placement_SaoPaulo_Case_1_2_cluster_intel-256_odcs_JOB11_Sim_2.sh /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Case_1_2_cluster_odcs
cp -f Placement_SaoPaulo_Case_1_2_cluster.yaml /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Case_1_2_cluster_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Case_1_2_cluster_odcs/JOB11/Sim_2 --seed=1013616942 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/SaoPaulo.csv --wcpu=0 --wodc=0 --wd=1 --odcs=328 > /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Case_1_2_cluster_odcs/JOB11/Sim_2.out 2>&1
