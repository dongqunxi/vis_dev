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
    #X = X.reshape(n_rois, n_rois-1)
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
    import mne
    from mne.stats import f_threshold_mway_rm, f_mway_rm, fdr_correction
    import matplotlib.pyplot as plt
    factor_levels = [2, 2]  # number of levels in each factor
    effects = 'A'  
    data = np.load(fncau_set)
    X = data[:, :, 0, :]
    fvals, pvals = f_mway_rm(X, factor_levels, effects=effects)
    def stat_fun(*args):
        return f_mway_rm(np.swapaxes(args, 1, 0), factor_levels=factor_levels,
                         effects=effects, return_pvals=False)[0]

    # The ANOVA returns a tuple f-values and p-values, we will pick the former.
    pthresh = 0.01  # set threshold rather high to save some time
    f_thresh = f_threshold_mway_rm(X.shape[0], factor_levels, effects,
                                pthresh)
    tail = 1  # f-test, so tail > 0
    n_permutations = 1000  # Save some time (the test won't be too sensitive ...)
    Y = X.swapaxes(1,0)
    m, n = Y.shape[:2]
    Y_power = Y.reshape(m, n, n_rois, (n_rois-1))
    T_obs, clusters, cluster_p_values, h0 = mne.stats.permutation_cluster_test(
        Y_power, stat_fun=stat_fun, threshold=f_thresh, tail=tail, n_jobs=1,
        n_permutations=n_permutations, buffer_size=None)
    
    
    ###############################################################################
    # Now using FDR:
    
    mask, _ = fdr_correction(pvals)
    T_obs_plot2 = np.ma.masked_array(T_obs, np.invert(mask))
    T_obs = recov_mat(T_obs, 1)
    T_obs_plot2 = recov_mat(T_obs_plot2, False)
    plt.figure()
    for f_image, cmap in zip([T_obs, T_obs_plot2], [plt.cm.gray, 'RdBu_r']):
        plt.imshow(f_image, cmap=cmap, extent=[1, 24, 1, 24], aspect='auto',
                origin='lower')
    
    plt.xlabel('Time (ms)')
    plt.ylabel('Frequency (Hz)')
    plt.title("Time-locked response for 'modality by location' \n"
            " FDR corrected (p <= 0.05)" )
    plt.show()
        
    