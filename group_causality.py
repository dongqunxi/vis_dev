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
out_path =  cau_path + 'causality/'
st_list = ['LLst', 'RRst', 'RLst',  'LRst']
nfreqs=[(4, 8), (8, 12), (12, 18), (18, 30), (30,45)]
#st_list = ['LLst']
# Stats set-up
prob = 0.5           # we assume the probability of chance
alpha = 0.01         # False alarm rate
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
    
    # reduce dignoal elements
    rd_counts = np.zeros((n_freqs, n_rois, n_rois-1))
    for i in range(n_rois):
        if (i-1 >= 0) and (i+1 < n_rois):
            rd_counts[:, i, :i] = counts[:, i,:i]
            rd_counts[:, i, i:] = counts[:, i, i+1:]
        elif (i-1) < 0:
            rd_counts[:, i, :] = counts[:, i, i+1:]
        elif (i+1) == n_rois:
            rd_counts[:, i, :] = counts[:, i,:i]

    # compute p-values
    pval = 1 - stats.binom.cdf(rd_counts, n_subj, prob)
    
    # use FDR to correct for multiple comparison
    reject_mask = np.zeros(pval.shape)
    for iroi in range(n_rois):
       reject_mask[:, iroi, :], _ = fdr_correction(pval[:, iroi, :], alpha) 
    #reject_mask, pval_fdr = fdr_correction(pval, alpha)
    
    # increase the dignoal elements and set them as False
    in_reject_mask = np.zeros((n_freqs, n_rois, n_rois))
    for i in range(n_rois):
        if (i-1 >= 0) and (i+1 < n_rois):
            in_reject_mask[:, i, :i] = reject_mask[:, i,:i]
            in_reject_mask[:, i, i] = False
            in_reject_mask[:, i, i+1:] = reject_mask[:, i, i:]
        elif (i-1) < 0:
            in_reject_mask[:, i, i] = False
            in_reject_mask[:, i, i+1:] = reject_mask[:, i, :]
        elif (i+1) == n_rois:
            in_reject_mask[:, i, :i] = reject_mask[:, i,:]
            in_reject_mask[:, i, i] = False
    
    # remove non-significant connections
    for isubj in range(n_subj):
        X[isubj] *= in_reject_mask
  
    Y = X.sum(axis=0)
    for ifreq in range(len(nfreqs)):
        fmin, fmax = nfreqs[ifreq][0], nfreqs[ifreq][1]
        np.save(out_path + '%s_%d_%dHz.npy' % (evt_st, fmin, fmax), Y[ifreq])
    #np.save(out_path+'%s_sigcaus.npy' %evt_st, X)


