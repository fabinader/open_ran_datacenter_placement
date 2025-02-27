#!/bin/bash
#SBATCH --time=1-0:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=preempt
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Brasilia_Magazine_Case_1_odcs/JOB14/Sim_1
cp -f run_Placement_Brasilia_Magazine_Case_1_amd-512_odcs_JOB14_Sim_1.sh /home/rqdfhsilva/CPQD/results_Placement_Brasilia_Magazine_Case_1_odcs
cp -f Placement_Brasilia_Magazine_Case_1.yaml /home/rqdfhsilva/CPQD/results_Placement_Brasilia_Magazine_Case_1_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Brasilia_Magazine_Case_1_odcs/JOB14/Sim_1 --seed=1215646073 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=3000 --population=300 --process=8 --wcpu=0 --wodc=0.1 --wd=0.9 --csv=/home/rqdfhsilva/CPQD/CityData/Brasilia.csv --wcpu=0 --wodc=0.2 --wd=0.8 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_Brasilia_Magazine_Case_1_odcs/JOB14/Sim_1.out 2>&1
