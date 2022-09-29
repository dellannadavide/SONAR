import time

import sys
import os

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to
# the sys.path.
sys.path.append(parent)

import utils.constants as Constants

from datetime import datetime
from pathlib import Path
import itertools as it
import subprocess


def submitJob(index_list, allNames, results_folder, all_experiments_timestamp, verbose, c_list):
    """
    Encoding the combination into a string of arguments
    """
    command_concat_str = ""
    exp_ind=0
    for c in c_list:
        exp_param_args = "exp_id=" + str(index_list[exp_ind]) + " "
        for i in range(len(allNames)):
            exp_param_args = exp_param_args + str(allNames[i]) + "=" + str(c[i]) + " "
        exp_param_args = exp_param_args + "results_folder=" + str(results_folder) + " all_experiments_timestamp=" + str(
            all_experiments_timestamp) + " verbose=" + str(verbose)
        # print(exp_param_args)
        command_concat_str = command_concat_str + ("" if (command_concat_str == "") else " &" ) + "python3 ./run_experiment_adaptation_commandline.py "+str(exp_param_args)
        exp_ind = exp_ind + 1

    p = subprocess.Popen('qsub', stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
    # Customize your options here
    job_name = "ca_%s_%d-%d" % (all_experiments_timestamp[-3:], index_list[0], index_list[-1])
    email = "d.dellanna@tudelft.nl"
    # walltime = "00:01:00"
    # processors = "nodes=1:ppn=%d" % len(index_list)
    processors = "nodes=1:ppn=20"
    command = command_concat_str + " & wait"



    job_string = """#!/bin/bash
       #PBS -N %s
       #PBS -m abe
       #PBS -M %s
       #PBS -l %s
       #PBS -o %s${PBS_JOBNAME}.o${PBS_JOBID}
       #PBS -e %s${PBS_JOBNAME}.e${PBS_JOBID}
       cd $PBS_O_WORKDIR
       trap 'echo "%s" >> %saborted.txt' TERM
       %s""" % (job_name, email, processors, results_folder,  results_folder, str(index_list[0])+"-"+str(index_list[-1]), results_folder, command)

    # Send job_string to qsub
    out, err = p.communicate(job_string.encode())
    # print(out)
    # print(str(index_list[0])+"-"+str(index_list[-1]))
    return out

def getNumberOfJobsRunning():
    qstat = subprocess.Popen(['qselect', '-u', 'ddellanna'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             shell=False)
    wc = subprocess.Popen(['wc', '-l'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=False)
    qstat_out, qstat_err = qstat.communicate()
    wc_out, wc_err = wc.communicate(qstat_out)
    return int(wc_out)

def main():
    """
        Step-based experiments.
        Define in the following the possible values of all variables to test
        """
    now = datetime.now()
    all_experiments_timestamp = str(now.strftime("%Y%m%d%H%M%S"))
    all_experiments_identifier = "exp"
    results_folder = "results/exp_" + all_experiments_identifier + "_" + all_experiments_timestamp + "/"
    Path(results_folder).mkdir(parents=True, exist_ok=True)
    verbose = Constants.VERBOSE_FALSE

    """ 
    Each of the following parameter values is a list, which can contain more than one value.
    If multiple values are expressed for different parameters, then all combinations of all expressed values are tried
    """

    exp_possible_val = {
        'society': ['Austria', 'US'],
        'dataset_file': ['data_USAustria_8000dp_v11_simple.xlsx'],
        'max_dataset_size': [1000, 10000],  # [1000, 8000, 16000], #[1000, 999999],
        'fuzzy_sets_file': ['fuzzy_sets_multiple_ref.xlsx'],
        'ling_vars_file': ['ling_var_multiple_ref.xlsx'],
        'rules_file_id': ['_ref_all_refined2'], # ['_ref_all'], ['_ref_all_refined']
        'interpretability_index': [Constants.PHI_INTERPRETABILITY_INDEX], # [Constants.PHI_INTERPRETABILITY_INDEX, Constants.AVG_COVERAGE_INDEX], #["Phi", "XP"],
        'min_nr_datapoints': [10, 50, 100],  # [1, 5, 10],
        'min_certainty_threshold': [0.0],  # [0.0, 0.05, 0.1, 0.15],
        'use_correct_interpretation': [False],  # [True, False],
        'consider_past_experience': [True, False],
        'genetic_algo': [Constants.GA],
        'ga_nr_gen': [100],
        'pop_size': [20],
        'contextualize': [False],  # [False, True],
        'min_nr_adaptations_for_contextualizing': [10],
        'trial': list(range(5))
    }
    # exp_possible_val = {
    #     'society': ['Austria', 'US'],
    #     'dataset_file': ['data_USAustria_10000dp_003p.xlsx'],
    #     'interpretability_index': ["Phi", "XP"],
    #     'min_nr_datapoints': [5],
    #     'min_certainty_threshold': [0.0],
    #     'genetic_algo': [Constants.GA],
    #     'ga_nr_gen': [10],
    #     'pop_size': [5],
    #     'trial': [0]
    # }

    """
        Here all the parameters expressed above are combined.
        Each of the possible combination is an experiment.
        Note that the parameter "trial" is included here. 
        By combining trial with the other parameters we obtain the repeated trials
        """
    exp_variating_param = []
    for k in exp_possible_val:
        if len(exp_possible_val[k]) > 1:
            exp_variating_param.append(k)
    allNames = sorted(exp_possible_val)
    combinations = it.product(*(exp_possible_val[Name] for Name in allNames))
    number_experiments = len(list(it.product(*(exp_possible_val[Name] for Name in allNames))))

    # print(allNames)
    # ind = 0
    # for c in combinations:
    #     print(ind, c)
    #     ind = ind+1
    # exit()

    """ Parameters for spliiting the jobs in batch based on the HPC capabilities and constraints.
        max_nr_experiments_per_batch determines the maximum number of experiments to put together in a batch (to be run concurrently)
        max_nr_batches, instead, determines how many batches/jobs should be sent to the HPC at a time.
        If more batches than max_nr_batches are required in total to run all experiments, 
        then the script will first send max_nr_batches first, then start a timer and every 5 minutes checks if some
        slots are available (i.e., if the current number of running jobs is < max_nr_batches) 
        and sends new jobs to fill the available slots, until all experiments are run. """
    max_number_experiments_per_batch = 1
    max_nr_batches = 10

    """ By tweaking the following two parameters it is possible to skip some of the experiments and repeat others
        (e.g., in case some of the jobs were killed and some particular exp need to be repeated).
        Example 1:
            out of 200 experiments, those with id 5, 6, 44 need to be repeated, while all the others were ok
            set
            index_first_exp = 500 (a value higher than 200, so that all the exp will be skipped expect for those to repeat)
            exp_to_repeat = [5,6,44]
        Example 2:
            out of 200 experiments, those with id 5, 6, 44 need to be repeated, as well as all starting from id 100
            set
            index_first_exp = 100 (the index of the first exp to execute)
            exp_to_repeat = [5,6,44]
        """
    index_first_exp = 0
    exp_to_repeat = []

    """ Based on the experiments, I create all batches.
         I obtain, 
         in var batches all batches to send, and
         in var batches_exp_indeces the indeces of the exp of all the experiments in each batch
         """
    batches = []
    batches_exp_indeces = []
    exp_index = 0
    batch = []
    exp_indeces = []
    for c in combinations:
        if (exp_index >= index_first_exp) or (exp_index in exp_to_repeat):
            if len(batch) < max_number_experiments_per_batch:  # if I can insert the current combination c in the current batch
                batch.append(c)
                exp_indeces.append(exp_index)
            else:  # otherwise I append the batch to the list of batches
                batches.append(batch)
                batches_exp_indeces.append(exp_indeces)
                # and I start creating the new one
                batch = [c]
                exp_indeces = [exp_index]
        exp_index = exp_index + 1
    # in case the last batch was not full and I didn't add it to the list of batches
    if len(batch) > 0:
        batches.append(batch)
        batches_exp_indeces.append(exp_indeces)
        batch = []
        exp_indeces = []

    """ Running """
    print("Running " + str(number_experiments) + " experiments in batches of max " + str(
        max_number_experiments_per_batch) + " [skipping the first " + str(index_first_exp - 1) + ", except for " + str(
        exp_to_repeat) + "]...")
    next_batch_to_submit = 0
    while next_batch_to_submit < len(batches):
        if getNumberOfJobsRunning() < max_nr_batches:
            jobid = submitJob(batches_exp_indeces[next_batch_to_submit], allNames, results_folder,
                              all_experiments_timestamp, verbose, batches[next_batch_to_submit])
            next_batch_to_submit = next_batch_to_submit + 1
        else:
            free_space = False
            while not free_space:
                time.sleep(60 * 5)  # wait 5 minutes
                if int(getNumberOfJobsRunning()) < max_nr_batches:
                    free_space = True










if __name__ == '__main__':
    main()
