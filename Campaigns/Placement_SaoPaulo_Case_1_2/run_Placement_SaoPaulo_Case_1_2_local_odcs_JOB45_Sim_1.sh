#!/bin/bash
mkdir -p /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_odcs/JOB45/Sim_1
cp -f run_Placement_SaoPaulo_Case_1_2_local_odcs_JOB45_Sim_1.sh /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_odcs
cp -f Placement_SaoPaulo_Case_1_2.yaml /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_odcs
cd '/home/oai-ufrn/Repositories/open_ran_datacenter_placement/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_odcs/JOB45/Sim_1 --seed=411778634 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/oai-ufrn/Repositories/open_ran_datacenter_placement/CityData/SaoPaulo.csv --wcpu=0 --wodc=0 --wd=1 --odcs=493 > /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_odcs/JOB45/Sim_1.out 2>&1
