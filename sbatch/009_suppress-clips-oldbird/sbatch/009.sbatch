#!/bin/bash

#BATCH --job-name=009
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=0:10:00
#SBATCH --mem=4GB
#SBATCH --output=slurm_009_%j.out

module purge

python ../src/009_suppress-clips-oldbird.py
