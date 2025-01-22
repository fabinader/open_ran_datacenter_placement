#!/bin/bash
mkdir -p /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB53/Sim_33
cp -f run_Placement_Curitiba_Conference_Paper_amd-3tb_odcs_JOB53_Sim_33.sh /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs
cp -f Placement_Curitiba_Conference_Paper.yaml /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs
cd '/home/oai-ufrn/Repositories/open_ran_datacenter_placement/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB53/Sim_33 --seed=3713743331 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/rqdfhsilva/CPQD/CityData/Curitiba.csv --wcpu=0.8 --wodc=0 --wd=0.2 --odcs=113 > /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_Curitiba_Conference_Paper_odcs/JOB53/Sim_33.out 2>&1
