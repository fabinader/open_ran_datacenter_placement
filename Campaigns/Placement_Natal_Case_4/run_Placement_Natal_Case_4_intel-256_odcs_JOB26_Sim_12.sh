#!/bin/bash
#SBATCH --time=1-12:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Natal_Case_4_odcs/JOB26/Sim_12
cp -f run_Placement_Natal_Case_4_intel-256_odcs_JOB26_Sim_12.sh /home/rqdfhsilva/CPQD/results_Placement_Natal_Case_4_odcs
cp -f Placement_Natal_Case_4.yaml /home/rqdfhsilva/CPQD/results_Placement_Natal_Case_4_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Natal_Case_4_odcs/JOB26/Sim_12 --seed=1282690575 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0.1 --wodc=0.1 --wd=0.8 --csv=/home/rqdfhsilva/CPQD/CityData/Natal.csv --wcpu=0.3 --wodc=0.5 --wd=0.2 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_Natal_Case_4_odcs/JOB26/Sim_12.out 2>&1
