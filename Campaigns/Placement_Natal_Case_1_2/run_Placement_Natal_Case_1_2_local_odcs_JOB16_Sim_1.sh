#!/bin/bash
mkdir -p /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Natal_Case_1_2_odcs/JOB16/Sim_1
cp -f run_Placement_Natal_Case_1_2_local_odcs_JOB16_Sim_1.sh /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Natal_Case_1_2_odcs
cp -f Placement_Natal_Case_1_2.yaml /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Natal_Case_1_2_odcs
cd '/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Natal_Case_1_2_odcs/JOB16/Sim_1 --seed=576274206 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/CityData/Natal.csv --wcpu=0 --wodc=0 --wd=1 --odcs=27 > /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Natal_Case_1_2_odcs/JOB16/Sim_1.out 2>&1
