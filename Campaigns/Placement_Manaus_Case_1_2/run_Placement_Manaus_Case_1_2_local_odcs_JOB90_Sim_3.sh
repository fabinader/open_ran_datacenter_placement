#!/bin/bash
mkdir -p /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Manaus_Case_1_2_odcs/JOB90/Sim_3
cp -f run_Placement_Manaus_Case_1_2_local_odcs_JOB90_Sim_3.sh /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Manaus_Case_1_2_odcs
cp -f Placement_Manaus_Case_1_2.yaml /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Manaus_Case_1_2_odcs
cd '/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/'
sleep $((11 + RANDOM % 50))
python3 odc_placement_parser.py --outputDir=/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Manaus_Case_1_2_odcs/JOB90/Sim_3 --seed=790554639 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/CityData/Manaus.csv --wcpu=0 --wodc=0 --wd=1 --odcs=22 > /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/results_Placement_Manaus_Case_1_2_odcs/JOB90/Sim_3.out 2>&1
