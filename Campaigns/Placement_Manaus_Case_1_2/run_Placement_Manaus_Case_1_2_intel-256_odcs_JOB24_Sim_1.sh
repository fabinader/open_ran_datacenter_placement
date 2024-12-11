#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Manaus_Case_1_2_odcs/JOB24/Sim_1
cp -f run_Placement_Manaus_Case_1_2_intel-256_odcs_JOB24_Sim_1.sh /home/rqdfhsilva/CPQD/results_Placement_Manaus_Case_1_2_odcs
cp -f Placement_Manaus_Case_1_2.yaml /home/rqdfhsilva/CPQD/results_Placement_Manaus_Case_1_2_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Manaus_Case_1_2_odcs/JOB24/Sim_1 --seed=3105180782 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Manaus.csv --wcpu=0 --wodc=0 --wd=1 --odcs=45 > /home/rqdfhsilva/CPQD/results_Placement_Manaus_Case_1_2_odcs/JOB24/Sim_1.out 2>&1
