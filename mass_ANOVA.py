import os, glob
import numpy as np

subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/individual_cau/'
st_list = ['LLst', 'RRst', 'LRst', 'RLst']
fncau_set = cau_path + 'cau_set.npy'
n_rois = 24
do_set = False
if do_set:
    sfreq=678.17
    freqs=[(4, 8), (8, 12), (12, 18), (18, 30), (30, 45)]
    path_list = glob.glob(cau_path+'/*[0-9]/')
    data = []
    for fn_path in path_list: 
        indi_mat = []
        for evt in st_list:
            fn_cau = fn_path + '%s_labels_ts,norm,cau.npy' %evt
            cau = np.load(fn_cau)
            nfft = cau.shape[-1]
            delta_F = sfreq / float(2 * nfft)
            nfreq = len(freqs)
            cau_bands = []
            for ifreq in range(nfreq):
                print 'Frequency index used..', ifreq
                fmin, fmax = int(freqs[ifreq][0] / delta_F), int(freqs[ifreq][1] /
                                                                delta_F)
                con_band = np.mean(cau[:, :, fmin:fmax + 1], axis=-1)
                np.fill_diagonal(con_band, 0)
                con_band = con_band.flatten()
                con_band = con_band[con_band.nonzero()]
                cau_bands.append(con_band)
            indi_mat.append(cau_bands)
        data.append(indi_mat)
    
    data = np.array(data)
    np.save(fncau_set, data)

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
    from mne.stats import f_threshold_mway_rm, f_mway_rm, fdr_correction
    import matplotlib.pyplot as plt
    factor_levels = [2, 2]  # number of levels in each factor
    effects = 'A*B'  
    data = np.load(fncau_set)
    fvals, pvals = f_mway_rm(data[:, :, 0, :], factor_levels, effects=effects)
    effect_labels = ['modality', 'location', 'modality by location']
    fn_labels = cau_path + 'func_list.npy'
    ROI_labels = np.load(fn_labels)
    # let's visualize our effects by computing f-images
    for effect, sig, effect_label in zip(fvals, pvals, effect_labels):
        plt.figure()
        # show naive F-values in gray
        plt.imshow(recov_mat(effect, 0), cmap=plt.cm.gray, extent=[1,
                24, 1, 24], aspect='auto',
                origin='lower')
                
        # create mask for significant Time-frequency locations
        effect = np.ma.masked_array(effect, [sig > .05])
        plt.imshow(recov_mat(effect, 0), cmap='RdBu_r', extent=[1,
                24, 1, 24], aspect='auto',
                origin='lower')
        plt.xticks(np.arange(len(ROI_labels))+1, ROI_labels, fontsize=5, rotation='vertical')
        plt.yticks(np.arange(len(ROI_labels))+1, ROI_labels, fontsize=5)
        plt.colorbar()
        plt.xlabel('ROIs')
        plt.ylabel('ROIs')
        plt.title(r"Time-locked response for '%s'" % (effect_label))
        plt.show()
        
    