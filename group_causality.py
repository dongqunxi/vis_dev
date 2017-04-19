''' 10 was estimated from Binomial statistical test, elements of group causal
matrices less than 10 were set as zeros. And was stored in <condition>_<fmin>_<fmax>.npy
Using FDR to corrected the group connections.  
'''
import os, glob
import numpy as np
from mne.stats import fdr_correction
import scipy.stats as stats

subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/stcs/' 
#st_list = ['LLst', 'RRst', 'RLst',  'LRst']
st_list = ['LLst']
# Stats set-up
prob = 0.5           # we assume the probability of chance
alpha = 0.05         # False alarm rate
# we need to load all data in one array as we later perform FDR correction
# the content of the data should be 1 (above surrogate) or 0 (below surrogate threshold

for evt_st in st_list:
    X = []
    fnsig_list = glob.glob(cau_path + '/*[0-9]/sig_cau/%s_sig_con_band.npy' %evt_st)
    for f in fnsig_list:
        sig_cau = np.load(f)
        print sig_cau.shape[-1]
        X.append(sig_cau)
        
    X = np.array(X)
    n_subj, n_freqs, n_rois, _ = np.shape(X)
    
    # count number of subjects showing a connection above surrogate
    counts = X.sum(axis=0)      # sum counts across subjects
    
    # compute minimum number of subjects needed for being significant
    thresh = stats.binom.ppf((1-alpha), n_subj, prob) + 1  # must be the next upper integer
    
    # zero those which are below the minimum expected number of subjects
    counts[counts < thresh] = 0   # not really necessary as we will reject this later with pval
    
    # compute p-values
    pval = 1 - stats.binom.cdf(counts, n_subj, prob)
    
    # use FDR to correct for multiple comparison
    reject_mask = np.zeros(pval.shape)
    for iroi in range(n_rois):
       reject_mask[:, iroi, :], _ = fdr_correction(pval[:, iroi, :], alpha) 
    #reject_mask, pval_fdr = fdr_correction(pval, alpha)
    
    
    # remove non-significant connections
    for isubj in range(n_subj):
        X[isubj] *= reject_mask


