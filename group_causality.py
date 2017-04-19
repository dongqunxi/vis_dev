''' 10 was estimated from Binomial statistical test, elements of group causal
matrices less than 10 were set as zeros. And was stored in <condition>_<fmin>_<fmax>.npy
Using FDR to corrected the group connections.  
'''
import os
import numpy as np
from mne.stats import fdr_correction
import scipy.stats as stats

subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/stcs/causality' 
X = np.load(cau_path + '/LLst_18_30Hz.npy')

pval = 1 - stats.binom.cdf(X, 13, 0.5)
reject_fdr, pval_fdr = fdr_correction(pval, alpha=0.05, method='indep')
n_rows = X.shape[0]
for i in range(n_rows):
    for j in range(n_rows):
        if i == j:
            continue
        if reject_fdr[i, j] == False:
            X[i, j] = 0

