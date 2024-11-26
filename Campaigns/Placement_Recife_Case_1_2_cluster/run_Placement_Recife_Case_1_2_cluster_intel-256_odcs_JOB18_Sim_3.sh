#!/bin/bash
#SBATCH --time=1-12:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
module load softwares/python/3.10.5-gnu8
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB18/Sim_3
cp -f run_Placement_Recife_Case_1_2_cluster_intel-256_odcs_JOB18_Sim_3.sh /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs
cp -f Placement_Recife_Case_1_2_cluster.yaml /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB18/Sim_3 --seed=756301332 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Recife.csv --wcpu=0 --wodc=0 --wd=1 --odcs=41 > /home/rqdfhsilva/CPQD/results_Placement_Recife_Case_1_2_cluster_odcs/JOB18/Sim_3.out 2>&1
