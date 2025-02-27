#!/bin/bash
#SBATCH --time=1-0:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=preempt
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Magazine_Case_1_odcs/JOB9/Sim_5
cp -f run_Placement_SaoPaulo_Magazine_Case_1_amd-512_odcs_JOB9_Sim_5.sh /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Magazine_Case_1_odcs
cp -f Placement_SaoPaulo_Magazine_Case_1.yaml /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Magazine_Case_1_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Magazine_Case_1_odcs/JOB9/Sim_5 --seed=233226471 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=3000 --population=300 --process=8 --wcpu=0 --wodc=0.1 --wd=0.9 --csv=/home/rqdfhsilva/CPQD/CityData/SaoPaulo.csv --wcpu=0 --wodc=0.6 --wd=0.4 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_SaoPaulo_Magazine_Case_1_odcs/JOB9/Sim_5.out 2>&1
