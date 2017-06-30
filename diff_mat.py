import numpy as np
import os
freqs = [(4, 8), (8, 12), (12, 18), (18, 30), (30, 45)]
st_list = ['LLst', 'RRst', 'LRst', 'RLst']
fr_csv = ['theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
subjects_dir = os.environ['SUBJECTS_DIR']
mat_dir = subjects_dir + 'fsaverage/stcs/causality/'
fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
       
#Normalize group causal matrices into 0-1 matrices
do_norm = False
if do_norm:
    for evt in st_list:
        i = 0
        for ifreq in freqs:
            fmin = ifreq[0]
            fmax = ifreq[1] 
            #fn_npy = '/home/uais/data/Chrono/18subjects/fsaverage/causality-GPDC/incon_con_%d-%dHz.npy' %(fmin, fmax)
            fn_npy = '/home/uais_common/dong/freesurfer/subjects/fsaverage/stcs/causality/%s_%d_%dHz.npy' %(evt, fmin, fmax)
            fn_path = os.path.split(fn_npy)[0]
            mat1 = np.load(fn_npy)
            mat1[mat1>0]=1
            fn_norm = fn_path+'/norm_%s_%d_%dHz.npy' %(evt, fmin, fmax)
            np.save(fn_norm, mat1)

#Find unque pathways in LR relative to LL, RL relative to RR
do_diff = True
if do_diff:
    import csv
    import matplotlib.pylab as plt
    incon_event=['LRst', 'RLst']
    con_event=['LLst', 'RRst']
    ROI_labels = np.load(fn_labels)
    for c in range(2):
        i = 0
        for ifreq in freqs:
            fmin = ifreq[0]
            fmax = ifreq[1] 
            fn_con = mat_dir + 'norm_%s_%d_%dHz.npy' % (con_event[c], fmin, fmax)
            fn_incon = mat_dir + 'norm_%s_%d_%dHz.npy' % (incon_event[c], fmin, fmax)
            incon_cau = np.load(fn_incon) 
            con_cau = np.load(fn_con)
            
            dif_cau = incon_cau - con_cau
            dif_cau[dif_cau < 0] = 0
            print 'diff_%s_%s_%s' %(incon_event[c], con_event[c], fr_csv[i])
            print '------------------------------'
            for inde in np.argwhere(dif_cau): 
                print 'From %s to %s' %(ROI_labels[inde[1]], ROI_labels[inde[0]])
            print ''
            fig_dif = mat_dir + 'diff_%s_%s_%s.jpg' %(incon_event[c], con_event[c], fr_csv[i])
            plt.matshow(dif_cau, interpolation='nearest')
            am_ROI = len(ROI_labels)
            plt.xticks(np.arange(am_ROI), ROI_labels, fontsize=9, rotation='vertical')
            plt.yticks(np.arange(am_ROI), ROI_labels, fontsize=9)
            plt.xlabel('diff_%s_%s_%s' %(incon_event[c], con_event[c], fr_csv[i]))
            plt.savefig(fig_dif, dpi=300)
            plt.close()

            csvfile = file(mat_dir + 'diff_%s_%s_%s.csv' %(incon_event[c], con_event[c], fr_csv[i]), 'wb')
            writer = csv.writer(csvfile)
            writer.writerows(dif_cau.T)
            i = i + 1
            
    