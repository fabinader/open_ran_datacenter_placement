#!/bin/bash

# Usage message
usage() {
  echo "Usage: $0 -j num_jobs -c cpus -d distance -C capacity -o odc -n campaign_name -w wcpu,wodc,wd"
  exit 1
}

# Initialize parameters
num_jobs=0
cpus=0
distance=0
capacity=0
odc=0
campaign_name=""
wcpu=0
wodc=0
wd=0

# Parse command line arguments
while getopts ":j:c:d:C:o:n:w:" opt; do
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
    n)
      campaign_name=$OPTARG
      ;;
    w)
      IFS=',' read -r wcpu wodc wd <<< "$OPTARG"
      ;;
    \?)
      usage
      ;;
  esac
done

# Check if all required parameters are provided
if [ $num_jobs -eq 0 ] || [ $cpus -eq 0 ] || [ $distance -eq 0 ] || [ $capacity -eq 0 ] || [ $odc -eq -1 ] || [ -z "$campaign_name" ] || [ -z "$wcpu" ] || [ -z "$wodc" ] || [ -z "$wd" ]; then
  usage
fi

# Base directory for the jobs
base_dir="$(dirname "$(readlink -f "$0")")"
campaign_dir="${base_dir}/Campaign_${campaign_name}"
data_dir="${campaign_dir}/data"

# Create campaign and data directories
mkdir -p "${data_dir}"

# Loop to create Job directories and run the script
for ((i=1; i<=num_jobs; i++))
do
  job_dir="${data_dir}/Job${i}"
  output_file="${data_dir}/Sim_${i}.out"
  mkdir -p "${job_dir}"
  python3 odc_placement_parser.py -c=${cpus} -d=${distance} -cp=${capacity} -t=60 -pop=300 -p=8 -o=${odc} -wcpu=${wcpu} -wodc=${wodc} -wd=${wd} -s=$i -opd="${job_dir}" > "${output_file}" 2>&1
done
