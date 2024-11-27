#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB7/Sim_6
cp -f run_Placement_Recife_Case_1_2_cluster_intel-256_odcs_JOB7_Sim_6.sh /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs
cp -f Placement_Recife_Case_1_2_cluster.yaml /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB7/Sim_6 --seed=1953404877 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Recife.csv --wcpu=0.5 --wodc=0 --wd=0.5 --odcs=55 > /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB7/Sim_6.out 2>&1
