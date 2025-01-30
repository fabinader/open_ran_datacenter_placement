#!/bin/bash
#SBATCH --time=0-1:0 #especifica o tempo máximo de execução do job, dado no padrão dias-horas:minutos
#SBATCH --mem=12228
mkdir -p /home/lance/CPQD_ODC_PLACEMENT/results_Placement_Curitiba_Test_odcs/JOB26/Sim_5
cp -f run_Placement_Curitiba_Test_amd-3tb_odcs_JOB26_Sim_5.sh /home/lance/CPQD_ODC_PLACEMENT/results_Placement_Curitiba_Test_odcs
cp -f Placement_Curitiba_Test.yaml /home/lance/CPQD_ODC_PLACEMENT/results_Placement_Curitiba_Test_odcs
cd '/home/lance/CPQD_ODC_PLACEMENT/'
sleep $((11 + RANDOM % 50))
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate py391
python3 odc_placement_parser.py --outputDir=/home/lance/CPQD_ODC_PLACEMENT/results_Placement_Curitiba_Test_odcs/JOB26/Sim_5 --seed=1282690575 --cpuper100=14 --maxdistance=11 --capacity=1000 --odcs=0 --trials=60 --population=300 --process=8 --wcpu=0 --wodc=0 --wd=1 --csv=/home/lance/CPQD_ODC_PLACEMENT/CityData/Curitiba.csv --wcpu=1 --wodc=0 --wd=0 --odcs=113 > /home/lance/CPQD_ODC_PLACEMENT/results_Placement_Curitiba_Test_odcs/JOB26/Sim_5.out 2>&1
