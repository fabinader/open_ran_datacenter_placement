#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Teste_Case_1_2_cluster_odcs/JOB42/Sim_3
cp -f run_Placement_Teste_Case_1_2_cluster_intel-256_odcs_JOB42_Sim_3.sh /home/rqdfhsilva/CPQD/results_Placement_Teste_Case_1_2_cluster_odcs
cp -f Placement_Teste_Case_1_2_cluster.yaml /home/rqdfhsilva/CPQD/results_Placement_Teste_Case_1_2_cluster_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate teste
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Teste_Case_1_2_cluster_odcs/JOB42/Sim_3 --seed=2379134625 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Recife.csv --wcpu=0 --wodc=0 --wd=1 --odcs=246 > /home/rqdfhsilva/CPQD/results_Placement_Teste_Case_1_2_cluster_odcs/JOB42/Sim_3.out 2>&1
