#!/bin/bash
#python3 odc_placement_parser.py -opd=/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/Job1 > /home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/Job1/Sim_0.out 2>&1


# Number of jobs to create
num_jobs=$1

# Base directory for the jobs
base_dir="/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement"

# Loop to create Job directories and run the script
for ((i=1; i<=num_jobs; i++))
do
  job_dir="${base_dir}/Job${i}"
  output_file="${job_dir}/Sim_${i}.out"
  mkdir -p "${job_dir}"
  python3 odc_placement_parser.py -c=16 -d=20 -cp=2560 -t=60 -pop=300 -p=8 -o=50 -wcpu=0.4 -wodc=0.4 -wd=0.2 -s=$i -opd="${job_dir}" > "${output_file}" 2>&1
done