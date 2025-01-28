#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Curitiba_Conference_Paper_odcs/JOB52/Sim_28
cp -f run_Placement_Curitiba_Conference_Paper_intel-256_odcs_JOB52_Sim_28.sh /home/rqdfhsilva/CPQD/results_Placement_Curitiba_Conference_Paper_odcs
cp -f Placement_Curitiba_Conference_Paper.yaml /home/rqdfhsilva/CPQD/results_Placement_Curitiba_Conference_Paper_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Curitiba_Conference_Paper_odcs/JOB52/Sim_28 --seed=2081915590 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Curitiba.csv --wcpu=0.7 --wodc=0 --wd=0.3 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_Curitiba_Conference_Paper_odcs/JOB52/Sim_28.out 2>&1
