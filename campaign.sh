#!/bin/bash

# Usage message
usage() {
  echo "Usage: $0 -j num_jobs -c cpus -d distance -C capacity -o odc"
  exit 1
}

# Initialize parameters
num_jobs=0
cpus=0
distance=0
capacity=0
odc=0

# Parse command line arguments
while getopts ":j:c:d:C:o:" opt; do
  case ${opt} in
    j)
      num_jobs=$OPTARG
      ;;
    c)
      cpus=$OPTARG
      ;;
    d)
      distance=$OPTARG
      ;;
    C)
      capacity=$OPTARG
      ;;
    o)
      odc=$OPTARG
      ;;
    \?)
      usage
      ;;
  esac
done

# Check if all required parameters are provided
if [ $num_jobs -eq 0 ] || [ $cpus -eq 0 ] || [ $distance -eq 0 ] || [ $capacity -eq 0 ] || [ $odc -eq -1 ]; then
  usage
fi

# Base directory for the jobs
base_dir="/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement"

# Loop to create Job directories and run the script
for ((i=1; i<=num_jobs; i++))
do
  job_dir="${base_dir}/Job${i}"
  output_file="${job_dir}/Sim_${i}.out"
  mkdir -p "${job_dir}"
  python3 odc_placement_parser.py -c=${cpus} -d=${distance} -cp=${capacity} -t=60 -pop=300 -p=8 -o=${odc} -wcpu=0.4 -wodc=0.4 -wd=0.2 -s=$i -opd="${job_dir}" > "${output_file}" 2>&1
done