#!/bin/bash
#SBATCH --time=1-0:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=preempt
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_Florianopolis_Magazine_Case_2_odcs/JOB88/Sim_1
cp -f run_Placement_Florianopolis_Magazine_Case_2_intel-128_odcs_JOB88_Sim_1.sh /home/rqdfhsilva/CPQD/results_Placement_Florianopolis_Magazine_Case_2_odcs
cp -f Placement_Florianopolis_Magazine_Case_2.yaml /home/rqdfhsilva/CPQD/results_Placement_Florianopolis_Magazine_Case_2_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_Florianopolis_Magazine_Case_2_odcs/JOB88/Sim_1 --seed=2269645511 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=1000 --population=300 --process=8 --wcpu=0.1 --wodc=0.1 --wd=0.8 --csv=/home/rqdfhsilva/CPQD/CityData/Florianopolis.csv --wcpu=0.1 --wodc=0.2 --wd=0.7 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_Florianopolis_Magazine_Case_2_odcs/JOB88/Sim_1.out 2>&1
