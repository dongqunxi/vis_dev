# -*- coding: utf-8 -*-
"""
=================================================================
Causality analysis
=================================================================
date: 22/02/2017

Before running this script, the absolute path of each ROI label
needs to be provided in the form of a text file,
'func_list.txt'/'func_label_list.txt'.
"""

# Authors: Dong Qunxi <dongqunxi@gmail.com>
#         Jürgen Dammers <j.dammers@fz-juelich.de>
# License: BSD (3-clause)

import os
import glob
import numpy as np
from apply_causality import apply_inverse_oper, apply_STC_epo
from apply_causality import (cal_labelts, normalize_data, sig_thresh,
                                   group_causality, model_order,
                                   model_estimation, causal_analysis, diff_mat)

print(__doc__)

# Set parameters
subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/stcs'
st_list = ['LLst', 'RRst', 'RLst',  'LRst']


sfreq = 678.17 # Sampling rate
#morder = 40 # Fixed model order
per = 99.99 # Percentile for causal surrogates
repeat = 1000
#ifre = int(sfreq / (2 * morder))
#freqs = [(ifre, 2*ifre), (2*ifre, 3*ifre), (3*ifre, 4*ifre), (4*ifre, 5*ifre)]
freqs = [(4, 8), (8, 12), (12, 18), (18, 30), (30, 45)]
# Cluster operation
do_apply_invers_oper = False # Making inverse operator
do_apply_STC_epo = False # Making STCs
do_extract_rSTCs = False
do_norm = False
do_morder = False
do_moesti = False
do_cau = False
#do_sig_thr = False
do_group = False
#do_group_plot = False
do_diff = False
plt_group_mat = True

###############################################################################
# Make inverse operator for each subject
# ------------------------------------------------
if do_apply_invers_oper:
    print '>>> Calculate Inverse Operator ....'
    #fn_list = glob.glob(subjects_dir + '*[0-9]/MEG/*rfDC,bcc,nr,ar,evt_*bc-epo.fif')
    fn_epo_list = glob.glob(subjects_dir+'/*[0-9]/MEG/*rfDC,bcc,nr,ar,evt_LLst_bc-epo.fif')
    apply_inverse_oper(fn_epo_list, subjects_dir=subjects_dir)
    print '>>> FINISHED with STC generation.'
    print ''

###############################################################################
# Makeing STCs
# ------------------------------------------------
if do_apply_STC_epo:
    print '>>> Calculate morphed STCs ....'
    for evt in st_list:
        fn_epo = glob.glob(subjects_dir+'/*[0-9]/MEG/*rfDC,bcc,nr,ar,evt_%s_bc-epo.fif' %evt)
        apply_STC_epo(fn_epo, event=evt, subjects_dir=subjects_dir)
    print '>>> FINISHED with morphed STC generation.'
    print ''
    
#########################################
# Extract representative STCs from ROIs
########################################
if do_extract_rSTCs:
    print '>>> Calculate representative STCs ....'
    func_list_file = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.txt'
    for evt_st in st_list:
        # Calculate the representative STCs(rSTCs) for each ROI.
        stcs_path = glob.glob(subjects_dir+'/fsaverage/stcs/*[0-9]/%s/' % evt_st)
        '''epo's time range is from -0.2~0.8s
        '''
        cal_labelts(stcs_path, func_list_file, condition=evt_st, 
                    min_subject='fsaverage', subjects_dir=subjects_dir)
    print '>>> FINISHED with rSTC generation.'
    print ''


# Normalization STCs
if do_norm:
    print '>>> Calculate normalized rSTCs ....'
    ts_path = glob.glob(subjects_dir+'/fsaverage/stcs/*[0-9]/*_labels_ts.npz')
    ts_path = sorted(ts_path)
    normalize_data(ts_path)
    print '>>> FINISHED with normalized rSTC generation.'
    print ''


# 1) Model construction and estimation
# 2) Causality analysis
if do_morder:
    print '>>> Calculate the optimized Model order....'
    fn_norm = glob.glob(subjects_dir+'/fsaverage/stcs/*[0-9]/*_labels_ts,norm.npy')
    # Get optimized model order using BIC
    fn_npyout = subjects_dir+'/fsaverage/stcs/bics_esti.jpg'
    model_order(fn_norm, p_max=100, fn_figout=fn_npyout)
    print '>>> FINISHED with optimized model order generation.'
    print ''

if do_moesti:
    print '>>> Envaluate the cosistency, whiteness, and stable features of the Model....'
    fn_monorm = glob.glob(subjects_dir+'/fsaverage/stcs/*[0-9]/*_labels_ts,norm.npz')
    fn_evalout = subjects_dir+'/fsaverage/stcs/estiMVAR.txt'
    #model_estimation(fn_monorm, morder=40)
    model_estimation(fn_monorm, fn_evalout)
    print '>>> FINISHED with the results of statistical tests generation.'
    print ''

if do_cau:
    print '>>> Make the causality analysis....'
    fn_monorm = glob.glob(subjects_dir+'/fsaverage/stcs/*[0-9]/*_labels_ts,norm.npz')
    fn_monorm = sorted(fn_monorm)
    # fn_monorm = glob.glob(cau_path + '/*[0-9]/*_labels_ts,norm.npy')
    #causal_analysis(fn_monorm[1:16], repeats=1000, morder=40, per=per, method='GPDC')
    fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
    ROIs_labels = np.load(fn_labels)
    causal_analysis(fn_monorm, ROIs=ROIs_labels, repeats=repeat, per=per, method='GPDC', msave=False)
    print '>>> FINISHED with causal matrices and surr-causal matrices generation.'
    print ''


#if do_sig_thr:
#    print '>>> Calculate the significance of the causality matrices....'
#    fn_cau = glob.glob(cau_path + '/*[0-9]/sig_cau_40/*,cau.npy')
#    sig_thresh(cau_list=fn_cau, per=per)
#    print '>>> FINISHED with significant causal matrices generation.'
#    print ''


if do_group:
    print '>>> Generate the group causal matrices....'
    for evt_st in st_list:
        out_path = cau_path + '/causality'
        fnsig_list = glob.glob(cau_path + '/*[0-9]/sig_cau_21/%s_sig_con_band.npy' %evt_st)
        fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
        ROIs_labels = np.load(fn_labels)
        group_causality(fnsig_list, evt_st, freqs, ROIs_labels, submount=11, out_path=out_path)
    print '>>> FINISHED with group causal matrices generation.'
    print ''


from apply_causality import plt_conditions
if plt_group_mat:
   out_path = cau_path + '/causality'
   fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
   ROIs_labels = np.load(fn_labels)
   plt_conditions(out_path, st_list, ROIs_labels, 9)
    
if do_diff:
    # Difference between incongruent and congruent tasks
    for ifreq in freqs:
        fmin = ifreq[0]
        fmax = ifreq[1]
        mat_dir = cau_path + '/causality'
        fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
        ROIs_labels = np.load(fn_labels)
        diff_mat(fmin=fmin, fmax=fmax, mat_dir=mat_dir, ROI_labels=ROIs_labels)
