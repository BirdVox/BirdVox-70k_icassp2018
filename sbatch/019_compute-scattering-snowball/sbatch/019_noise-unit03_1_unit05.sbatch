#!/bin/bash

#BATCH --job-name=019_noise-unit03_1_unit05
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=12:00:00
#SBATCH --mem=1GB
#SBATCH --output=../slurm/slurm_019_noise-unit03_1_unit05_%j.out

module purge
module load matlab/2017a

# The first argument is the name of the augmentation.
# The second argument is the instance ID of the augmentation.
# The third argument is the name of the recording unit.
python ../../../src/019_compute-scattering-snowball.py noise-unit03 1 unit05