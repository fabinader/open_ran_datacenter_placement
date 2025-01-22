#!/bin/bash
mkdir -p /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB95/Sim_31
cp -f run_Placement_Curitiba_Conference_Paper_amd-3tb_odcs_JOB95_Sim_31.sh /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs
cp -f Placement_Curitiba_Conference_Paper.yaml /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs
cd '/home/oai-ufrn/Repositories/open_ran_datacenter_placement/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB95/Sim_31 --seed=4176769362 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Curitiba.csv --wcpu=0.7 --wodc=0 --wd=0.3 --odcs=57 > /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB95/Sim_31.out 2>&1
