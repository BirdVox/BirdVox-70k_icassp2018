#!/bin/bash

#BATCH --job-name=067_aug-none_test-unit05_trial-6
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00
#SBATCH --mem=64GB
#SBATCH --output=../slurm/slurm_067_aug-none_test-unit05_trial-6_%j.out

module purge

# The argument is the kind of data augmentation.
python ../../../src/067_evaluate-pcen-convnet-full-audio-nomindist.py none unit05 6