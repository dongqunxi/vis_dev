''' This script referred the script:plot_stats_cluster_time_frequency_repeated_measures_anova.py
    ----------------------------------------------------------------------------
    We have two different modalities (congruent and incongruent) and we have two
    different stimulus location (left and right) we define:
    Modality: A1: congruent A2: incongruent
    Location: B1: stimulus location left B2: stimulus location right
'''
import os
import numpy as np
from mne.stats import f_mway_rm, fdr_correction
import matplotlib.pyplot as plt

subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/individual_cau/'
n_rois = 24

fncau_set = cau_path + 'cau_set.npy'
''' 'data' is a matrix (subjects, conditions, frequency_bands, GPDC_values),
     the order of 'conditions' is: 'LL', 'RR', 'LR', 'RL'.
     the order of 'frequency_bands' is: 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma'
     the 'GPDC_values' is one array with size 24*(24-1) by rejecting the diagonal elements. 
'''
data = np.load(fncau_set)


def recov_mat(X, diag):
    # increase the dignoal elements and set them as False
    X = X.reshape(n_rois, n_rois-1)
    new_X = np.zeros((n_rois, n_rois))
    for i in range(n_rois):
         if (i-1 >= 0) and (i+1 < n_rois):
             new_X[i, :i] = X[i,:i]
             new_X[i, i] = diag
             new_X[i, i+1:] = X[i, i:]
         elif (i-1) < 0:
             new_X[i, i] = diag
             new_X[i, i+1:] = X[i, :]
         elif (i+1) == n_rois:
             new_X[i, :i] = X[i,:]
             new_X[i, i] = diag
    return new_X
             
do_anova = True
if do_anova:
    X = data[:, :, 2, :] # Make M-way ANOVA estimates for some frequency band
    factor_levels = [2, 2]  # number of levels in each factor
    effects = 'A' # Estimate the conflict effect
    fn_labels = cau_path + 'func_list.npy'
    ROI_labels = np.load(fn_labels)
    #Compute M-way repeated measures ANOVA for fully balanced designs.
    fvals, pvals = f_mway_rm(X, factor_levels, effects=effects)
    # Now using FDR to correct pvals
    mask, _ = fdr_correction(pvals)
    
    # Recover mask matrix and plot
    r_mask = recov_mat(mask, False)
    cax = plt.matshow(r_mask, interpolation='nearest')
    plt.xticks(np.arange(len(ROI_labels)), ROI_labels, rotation='vertical')
    plt.yticks(np.arange(len(ROI_labels)), ROI_labels)
    plt.show()
    