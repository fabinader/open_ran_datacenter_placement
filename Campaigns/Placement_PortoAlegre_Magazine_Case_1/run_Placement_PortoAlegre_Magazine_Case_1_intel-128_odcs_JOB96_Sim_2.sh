#!/bin/bash
#SBATCH --time=1-0:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --qos=preempt
mkdir -p /home/rqdfhsilva/CPQD/results_Placement_PortoAlegre_Magazine_Case_1_odcs/JOB96/Sim_2
cp -f run_Placement_PortoAlegre_Magazine_Case_1_intel-128_odcs_JOB96_Sim_2.sh /home/rqdfhsilva/CPQD/results_Placement_PortoAlegre_Magazine_Case_1_odcs
cp -f Placement_PortoAlegre_Magazine_Case_1.yaml /home/rqdfhsilva/CPQD/results_Placement_PortoAlegre_Magazine_Case_1_odcs
cd '/home/rqdfhsilva/CPQD/'
sleep $((11 + RANDOM % 50))
eval "$(conda shell.bash hook)"
conda activate cpqd
python3 odc_placement_parser.py --outputDir=/home/rqdfhsilva/CPQD/results_Placement_PortoAlegre_Magazine_Case_1_odcs/JOB96/Sim_2 --seed=694986042 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=1000 --population=300 --process=8 --wcpu=0 --wodc=0.1 --wd=0.9 --csv=/home/rqdfhsilva/CPQD/CityData/PortoAlegre.csv --wcpu=0 --wodc=0.3 --wd=0.7 --odcs=0 > /home/rqdfhsilva/CPQD/results_Placement_PortoAlegre_Magazine_Case_1_odcs/JOB96/Sim_2.out 2>&1
