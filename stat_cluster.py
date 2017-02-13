
import os
import numpy as np
#from scipy import stats as stats
#import glob

import mne
from mne import (spatial_tris_connectivity,
                 grade_to_tris)
from mne.stats import (spatio_temporal_cluster_1samp_test,
                       summarize_clusters_stc, spatio_temporal_cluster_test)

from jumeg.jumeg_preprocessing import get_files_from_list
from scipy import stats as stats

def reset_directory(path=None):
    """
    check whether the directory exits, if yes, recreat the directory
    ----------
    path : the target directory.
    """
    import shutil
    isexists = os.path.exists(path)
    if isexists:
        shutil.rmtree(path)
    os.makedirs(path)


def set_directory(path=None):
    """
    check whether the directory exits, if no, creat the directory
    ----------
    path : the target directory.

    """
    isexists = os.path.exists(path)
    if not isexists:
        os.makedirs(path)
        
def find_files(rootdir='.', pattern='*'):
    import os, fnmatch
    files = []
    for root, dirnames, filenames in os.walk(rootdir):
      for filename in fnmatch.filter(filenames, pattern):
          files.append(os.path.join(root, filename))

    files = sorted(files)

    return files
                
def apply_inverse_ave(fnevo, subjects_dir):
    ''' Make individual inverse operator.

        Parameter
        ---------
        fnevo: string or list
            The evoked file with ECG, EOG and environmental noise free.
        subjects_dir: The total bath of all the subjects.

    '''
    from mne import make_forward_solution
    from mne.minimum_norm import make_inverse_operator, write_inverse_operator
    fnlist = get_files_from_list(fnevo)

    # loop across all filenames
    for fname in fnlist:
        fn_path = os.path.split(fname)[0]
        name = os.path.basename(fname)
        subject = name.split('_')[0]
        fn_inv = fn_path + '/%s_fibp1-45,ave-inv.fif' % subject
        subject_path = subjects_dir + '/%s' % subject

        fn_trans = fn_path + '/%s-trans.fif' % subject
        fn_cov = fn_path + '/%s_empty,fibp1-45-cov.fif' % subject
        fn_src = subject_path + '/bem/%s-ico-5-src.fif' % subject
        fn_bem = subject_path + '/bem/%s-5120-5120-5120-bem-sol.fif' % subject
        [evoked] = mne.read_evokeds(fname)
        evoked.pick_types(meg=True, ref_meg=False)
        noise_cov = mne.read_cov(fn_cov)
        # noise_cov = dSPM.cov.regularize(noise_cov, evoked.info,
        #                               mag=0.05, grad=0.05, proj=True)
        fwd = make_forward_solution(evoked.info, fn_trans, fn_src, fn_bem)
        fwd['surf_ori'] = True
        inv = make_inverse_operator(evoked.info, fwd, noise_cov, loose=0.2,
                                    depth=0.8, limit_depth_chs=False)
        write_inverse_operator(fn_inv, inv)


def apply_STC_ave(fnevo, method='dSPM', snr=3.0):
    ''' Inverse evoked data into the source space.
        Parameter
        ---------
        fnevo: string or list
            The evoked file with ECG, EOG and environmental noise free.
        method:string
            Inverse method, 'dSPM' or 'mne'
        snr: float
            Signal to noise ratio for inverse solution.
    '''
    #Get the default subjects_dir
    from mne.minimum_norm import apply_inverse, read_inverse_operator
    fnlist = get_files_from_list(fnevo)
    # loop across all filenames
    for fname in fnlist:
        name = os.path.basename(fname)
        fn_path = os.path.split(fname)[0]
        fn_stc = fname[:fname.rfind('-ave.fif')]
        # fn_inv = fname[:fname.rfind('-ave.fif')] + ',ave-inv.fif'
        subject = name.split('_')[0]
        fn_inv = fn_path + '/%s_fibp1-45,ave-inv.fif' % subject
        snr = snr
        lambda2 = 1.0 / snr ** 2
        # noise_cov = mne.read_cov(fn_cov)
        [evoked] = mne.read_evokeds(fname)
        evoked.pick_types(meg=True, ref_meg=False)
        inv = read_inverse_operator(fn_inv)
        stc = apply_inverse(evoked, inv, lambda2, method,
                            pick_ori='normal')
        stc.save(fn_stc)


def morph_STC(fn_list, method, template='fsaverage', btmin=-0.3, btmax=0., 
               subjects_dir=None):
    '''
        Morph individual STC into the common brain space.

        Parameter
        ------------------------------------
        fn_list: list
            The paths of the individual STCs.
        subjects_dir: The total bath of all the subjects.
        template: string
            The subject name as the common brain.
        btmin, btmax: float
            If 'baseline' is True, baseline is croped using this period.

    '''
    from mne import read_source_estimate, morph_data
    for fname in fn_list:
        name = os.path.basename(fname)
        subject = name.split('_')[0]
        cond = name.split('_')[-2]
        import pdb
        pdb.set_trace()
        stc_name = name[:name.rfind('-lh.stc')]
        min_dir = subjects_dir + '/%s' % template
        # this path used for ROI definition
        stc_path = min_dir + '/%_ROIs/%s' % (method, subject)
        # fn_cov = meg_path + '/%s_empty,fibp1-45,nr-cov.fif' % subject
        set_directory(stc_path)
        # Morph STC
        stc = read_source_estimate(fname)
        stc_morph = morph_data(subject, template, stc, grade=5, subjects_dir=subjects_dir)
        stc_morph.save(stc_path + '/%s' % (stc_name), ftype='stc')
        if cond[2:] == 'st':
            stc_base = stc_morph.crop(btmin, btmax)
            stc_base.save(stc_path + '/%s_%s_baseline' % (subject, cond[:2]),
                          ftype='stc')
                          
#################################################################################
# Spatial clustering
#################################################################################
    
def Ara_norm(subjects, ncond, stcs_dir, out_path):
    ''' 
        Arange group arrays for pre vs post stimulus, zscore them and make
        abs.
        
        Parameters:
        --------------
        subjects: list,
            the subjects list.
        ncond: int,
            the amount of experimental conditions.
        stcs_dir: string,
            the path for searching stcs of each condition.
        out_path: string,
            the path for storing group z-sored arrays.
    '''
    nsubjects = len(subjects)
    fn_list = find_files(stcs_dir, pattern='*evt*_bc-lh.stc') 
    fn_list = np.reshape(fn_list,(nsubjects,ncond)) 
    for icond in range(ncond):
        fn_tmp = fn_list[0, icond]
        name = os.path.basename(fn_tmp)
        cond = name.split('_')[-2]
        A_evt = []
        A_base = []
        for isubj in range(nsubjects):
            fn_stc = fn_list[isubj, icond]
            name = os.path.basename(fn_stc)
            stc = mne.read_source_estimate(fn_stc)
            if cond[2:] == 'st':
                stc.crop(0, 0.3)
            elif cond[2:] == 'rt':
                stc.crop(-0.2, 0.1)
            #data = stc.data.flatten()
            data = stc.data
            path = os.path.dirname(fn_stc)
            subject = name.split('_')[0]
            fn_base = path + '/%s_%s_baseline-lh.stc' %(subject, cond[:2])
            base_stc = mne.read_source_estimate(fn_base)
            base_data = base_stc.data
            b_mean = base_data.mean()
            b_std = base_data.std()
            
            #z-score pre and post data
            data = (data - b_mean) / b_std
            base_data = (base_data - b_mean) / b_std
            A_evt.append(data)
            A_base.append(base_data)
              
        A_evt = np.array(A_evt)
        A_base = np.array(A_base)
        #print cond, np.percentile(np.abs(A_base), 95)
        tstep = stc.tstep
        fsave_vertices = stc.vertices
        ctime = min([A_evt.shape[-1], A_base.shape[-1]])
        times = stc.times[:ctime]
        X = [A_evt[:, :, :ctime], A_base[:, :, :ctime]]
        
        del A_evt, A_base
        # save data matrix
        X = np.array(X)
        #X = np.abs(X)  # only magnitude # don't do this here
        X = X.transpose(0,1,3,2)
        np.savez(out_path + 'Group_%s.npz' % (cond), X=X, tstep=tstep, times=times,
                 fsave_vertices=fsave_vertices)
        del X
                    
def exclu_vers(subjects_dir):
    ''' Exclude the vertices of the medial wall.
    '''    
    fn_lmedial = subjects_dir + 'fsaverage/label/lh.Medial_wall.label'
    lh_medial = mne.read_label(fn_lmedial)
    lh_mvers = lh_medial.get_vertices_used()
    fn_rmedial = subjects_dir + 'fsaverage/label/rh.Medial_wall.label'
    rh_medial = mne.read_label(fn_rmedial)
    rh_mvers = rh_medial.get_vertices_used()
    rh_mvers = rh_mvers + 10242
    del_vers = list(lh_mvers) + list(rh_mvers)
    return del_vers

def sample1_clus_thr(fn_list, n_per=8192, pthr=0.001, p=0.01, tail=1,  del_vers=None, n_jobs=1):
    '''
      Calculate significant clusters using 1sample ttest.

      Parameter
      ---------
      fn_list: list
        Paths of group arrays
      n_per: int
        The permutation for ttest.
      pct: int or float.
        The percentile of the baseline distribution.
      p: float
        The corrected p_values for comparisons.
      tail: 1 or 0
        if tail=1, that is 1 tail test
        if tail=0, that is 2 tail test 
      del_vers: None or _exclu_vers
        If is '_exclu_vers', delete the vertices in the medial wall.
    '''

    print('Computing connectivity.')
    connectivity = spatial_tris_connectivity(grade_to_tris(5))

    # Using the percentile of baseline array as the distribution threshold
    for fn_npz in fn_list:
        
        npz = np.load(fn_npz)
        tstep = npz['tstep'].flatten()[0]
        #    Note that X needs to be a multi-dimensional array of shape
        #    samples (subjects) x time x space, so we permute dimensions
        X = npz['X']
        #X_b = X[1]
        X = X[0]
        fn_path = os.path.dirname(fn_npz)
        name = os.path.basename(fn_npz)
        n_subjects = X.shape[0]
        if tail == 1:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_pthr%.3f.npz' %(n_per, tail, pthr)
            X = np.abs(X)
            t_threshold = -stats.distributions.t.ppf(0.01, n_subjects-1)
        elif tail == 0:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_pthr%.3f.npz' %(n_per, tail+2, pthr)
            t_threshold = -stats.distributions.t.ppf(pthr/2, n_subjects-1)
            
        fsave_vertices = [np.arange(X.shape[-1]/2), np.arange(X.shape[-1]/2)]
    
        #n_subjects = X.shape[0]
        #t_threshold = -stats.distributions.t.ppf(0.01/(1+(tail==0)), n_subjects-1)

        print('Clustering.')
        T_obs, clusters, cluster_p_values, H0 = clu = \
            spatio_temporal_cluster_1samp_test(X, connectivity=connectivity,
                                            n_jobs=n_jobs, threshold=t_threshold,
                                            n_permutations=n_per, tail=tail, spatial_exclude=del_vers)
    
        #    Now select the clusters that are sig. at p < 0.05 (note that this value
        #    is multiple-comparisons corrected).
        good_cluster_inds = np.where(cluster_p_values < p)[0]
        print 'the amount of significant clusters are: %d' %good_cluster_inds.shape
    
        # Save the clusters as stc file
        np.savez(fn_out, clu=clu, tstep=tstep, fsave_vertices=fsave_vertices)
        assert good_cluster_inds.shape != 0, ('Current p_threshold is %f %pthr,\
                                    maybe you need to reset a lower p_threshold')

def sample1_clus_fixed(fn_list, n_per=8192, thre=5.3, p=0.01, tail=1,  del_vers=None, n_jobs=1, max_step=30):
    '''
      Calculate significant clusters using 1sample ttest.

      Parameter
      ---------
      fn_list: list
        Paths of group arrays
      n_per: int
        The permutation for ttest.
      pct: int or float.
        The percentile of the baseline distribution.
      p: float
        The corrected p_values for comparisons.
      tail: 1 or 0
        if tail=1, that is 1 tail test
        if tail=0, that is 2 tail test 
      del_vers: None or _exclu_vers
        If is '_exclu_vers', delete the vertices in the medial wall.
    '''

    print('Computing connectivity.')
    connectivity = spatial_tris_connectivity(grade_to_tris(5))

    # Using the percentile of baseline array as the distribution threshold
    for fn_npz in fn_list:
        
        npz = np.load(fn_npz)
        tstep = npz['tstep'].flatten()[0]
        #    Note that X needs to be a multi-dimensional array of shape
        #    samples (subjects) x time x space, so we permute dimensions
        X = npz['X']
        X = X[0]
        fn_path = os.path.dirname(fn_npz)
        name = os.path.basename(fn_npz)
        t_threshold = thre
        if tail == 1:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_thr%.2f.npz' %(n_per, tail, thre)
            X = np.abs(X)
        elif tail == 0:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_thr%.2f.npz' %(n_per, tail+2, thre)
            
        fsave_vertices = [np.arange(X.shape[-1]/2), np.arange(X.shape[-1]/2)]
    
        #n_subjects = X.shape[0]
        #t_threshold = -stats.distributions.t.ppf(0.01/(1+(tail==0)), n_subjects-1)

        print('Clustering.')
        T_obs, clusters, cluster_p_values, H0 = clu = \
            spatio_temporal_cluster_1samp_test(X, connectivity=connectivity,
                                            n_jobs=n_jobs, threshold=t_threshold,
                                            n_permutations=n_per, tail=tail, max_step=max_step, spatial_exclude=del_vers)
    
        #    Now select the clusters that are sig. at p < 0.05 (note that this value
        #    is multiple-comparisons corrected).
        good_cluster_inds = np.where(cluster_p_values < p)[0]
        print 'the amount of significant clusters are: %d' %good_cluster_inds.shape
    
        # Save the clusters as stc file
        np.savez(fn_out, clu=clu, tstep=tstep, fsave_vertices=fsave_vertices)
        assert good_cluster_inds.shape != 0, ('Current p_threshold is %f %p_thr,\
                                    maybe you need to reset a lower p_threshold')


def cluster_info(T_obs, clusters, cluster_p_values, clu_thresh, min_duration,
                 data=None, times=None, label='UnKonwn', p_accept=0.01, fnout=None):
    '''
    Extract information about the cluster test.

    Parameter
    ---------

    T_obs: [n_times, n_vertices], as returned from the spatio-temporal cluster test

    clusters: [n_clusters, 2]  for each cluster we have space and time indices

    cluster_p_values: [n_clusters]

    clu_thresh: threshold (i.e. sign. level) to find clusters across space and time

    times: optional
        STC time array (e.g. stc.times) in ms
        if not set, sample index is used instead (note info will still be in ms)

    grand_avg: optional
        group averaged signal that was used for the spatio-temporal cluster test
        shape: [n_times, n_vertices]
        in case of a 1-sample test, these are the group averaged post-stim signals X
        in case of a 2-sample test, these are the group averaged contrast data
        e.g., contrast = np.abs(X[0].mean(axis=0) - X[1].mean(axis=0))

    p_accept: p-value that defines the corrected p-value

    fnout: if set, statistics will be saved
    '''

    import numpy as np

    good_cluster_inds = np.where(cluster_p_values < p_accept)[0]

    n_times, n_vert = T_obs.shape
    n_cluster = len(cluster_p_values)
    n_good = len(good_cluster_inds)

    if not np.any(times):
        times = np.arange(n_times)
    t_step = times[1] - times[0]

    txt = ['\n']
    txt.append('>>> Cluster statistics:\n')
    txt.append('cluster stat label: %s\n' % label)
    txt.append('cluster threshold  %f\n' % clu_thresh)
    txt.append('number of all clusters found: %d\n' % n_cluster)
    txt.append('cluster p-value (sig. level) %0.6f\n' % p_accept)
    txt.append('number of significant clusters found: %d\n' % n_good)
    txt.append('smallest p-value found: %0.6f\n' % cluster_p_values.min())
    txt.append('largest  p-value found (below sig. level): %0.6f\n' % cluster_p_values[good_cluster_inds].max())
    txt.append('number of vertices and time points: %d , %d\n\n' % (n_vert, n_times))
    txt.append('time step used for cluster analysis: %f\n' % t_step)
    txt.append('=========================================================================\n')

    if n_good > 0:
        for i_clu, clu_idx in enumerate(good_cluster_inds):

            # unpack cluster information, get unique indices
            idx_time, idx_space = np.squeeze(clusters[clu_idx])
            idx_space = np.unique(idx_space)
            idx_time = np.unique(idx_time)
            nsig_time = len(idx_time)
            nsig_space = len(idx_space)
            nsig_val = nsig_time * nsig_space

            # time range of significant values
            times_sig = times[idx_time]
            ix_t1 = times_sig.argmin()
            ix_t2 = times_sig.argmax()
            sig_tstart = times_sig[ix_t1]  # in ms
            sig_tend = times_sig[ix_t2]  # in ms
            sig_duration = (ix_t2 - ix_t1) * t_step  # in ms
                
            # sig. stat. values (t- or F stat) over space and time
            stats = T_obs[:, idx_space]
            stats = stats[idx_time, :]
            stats_min = stats.min()
            stats_max = stats.max()
            stats_mean = stats.mean()
            stats_max_alltimes = stats.max(axis=1)
            ix_tmax = stats_max_alltimes.argmax()
            time_max = times[idx_time[ix_tmax]]
            # Group averaged signal data
            if np.any(data):
                sigpow = data[:, idx_space]
                sigpow = sigpow[idx_time, :]
                sigpow_min = sigpow.min()
                sigpow_max = sigpow.max()
                sigpow_mean = sigpow.mean()

                sigpow_min_tmax = sigpow[ix_tmax].min()
                sigpow_max_tmax = sigpow[ix_tmax].max()
                sigpow_mean_tmax = sigpow[ix_tmax].mean()

            # write info
            txt.append('\n')
            txt.append('Cluster #%d - stats on significant values\n' % (i_clu + 1))
            txt.append('cluster p-value: %0.3f\n' % cluster_p_values[clu_idx])
            txt.append('number of sig. time points with p<%0.2f:  %d\n' % (p_accept, nsig_time))
            txt.append('number of sig. vertices    with p<%0.2f:  %d\n' % (p_accept, nsig_space))
            txt.append('number of values           with p<%0.2f:  %d\n' % (p_accept, nsig_val))
            txt.append('time window of sig. values [ms]: tmin = %d, tmax= %d\n' % (sig_tstart, sig_tend))
            txt.append('      duration of cluster activity [ms]: duration = %d\n' % sig_duration)
            if sig_duration < min_duration:
                print sig_duration
                cluster_p_values[clu_idx] = 1
                txt.append('      Since its duration lower than %dms, it is rejected' % min_duration)
            txt.append('T/F-values in cluster:\n')
            txt.append('   min = %0.2f\n' % stats_min)
            txt.append('   max = %0.2f\n' % stats_max)
            txt.append('   mean = %0.2f\n' % stats_mean)
            txt.append('   time of max value = %d\n' % time_max)
            if np.any(data):
                txt.append('Data values in cluster over all time points:\n')
                txt.append('   min = %f\n' % sigpow_min)
                txt.append('   max = %f\n' % sigpow_max)
                txt.append('   mean = %f\n' % sigpow_mean)
                txt.append('Data values in cluster at tmax:\n')
                txt.append('   min = %f\n' % sigpow_min_tmax)
                txt.append('   max = %f\n' % sigpow_max_tmax)
                txt.append('   mean = %f\n' % sigpow_mean_tmax)
                txt.append('-------------------------------------------------------------------------\n')

    if fnout:
        fid = open(fnout, "w")
        fid.writelines(txt)
        fid.close()

    return cluster_p_values


def sample1_clus(fn_list, n_per=8192, pct=99, p=0.01, tail=1,  min_duration=20, del_vers=None, n_jobs=1):
    '''
      Calculate significant clusters using 1sample ttest.

      Parameter
      ---------
      fn_list: list
        Paths of group arrays
      n_per: int
        The permutation for ttest.
      pct: int or float.
        The percentile of the baseline distribution.
      p: float
        The corrected p_values for comparisons.
      tail: 0 or 1.
        0 stands for 2-tailed test, 1 stands for 1-tailed test.
      min_duration: int or float.
        The minimum duration of significant clusters (ms).
      del_vers: None or _exclu_vers
        If is '_exclu_vers', delete the vertices in the medial wall.
    '''

    print('Computing connectivity.')
    connectivity = spatial_tris_connectivity(grade_to_tris(5))

    # Using the percentile of baseline array as the distribution threshold
    for fn_npz in fn_list:
        
        npz = np.load(fn_npz)
        tstep = npz['tstep'].flatten()[0]
        #    Note that X needs to be a multi-dimensional array of shape
        #    samples (subjects) x time x space, so we permute dimensions
        X = npz['X']
        times = npz['times'] * 1000 # times in ms
        X_b = X[1]
        X = X[0]
        fn_path = os.path.dirname(fn_npz)
        name = os.path.basename(fn_npz)
        
        if tail == 1:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_pct%.3f_%.1f.npz' %(n_per, tail, pct, min_duration)
            X = np.abs(X)
            t_threshold = np.percentile(np.abs(X_b), pct)
        elif tail == 0:
            fn_out = fn_path + '/clu1sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_pct%.3f_%.1f.npz' %(n_per, tail+2, pct, min_duration)
            t_threshold = np.percentile(X_b, pct)
            
        fsave_vertices = [np.arange(X.shape[-1]/2), np.arange(X.shape[-1]/2)]
    
        #n_subjects = X.shape[0]
        #t_threshold = -stats.distributions.t.ppf(0.01/(1+(tail==0)), n_subjects-1)

        print('Clustering.')
        T_obs, clusters, cluster_p_values, H0 = clu = \
            spatio_temporal_cluster_1samp_test(X, connectivity=connectivity,
                                            n_jobs=n_jobs, threshold=t_threshold,
                                            n_permutations=n_per, tail=tail, spatial_exclude=del_vers)
    
        good_cluster_inds = np.where(cluster_p_values < p)[0]
        print 'the amount of significant clusters are: %d' %good_cluster_inds.shape
        
        # Record the information of the clusters
        name = os.path.basename(fn_npz).split('_')[-1]
        cond = name[:name.rfind('.npz')]
        fn_out1 = fn_npz[:fn_npz.rfind('.npz')] + ',1sample,clus_info.txt'
        data = np.abs(X.mean(axis=0))
        cluster_pvalues = cluster_info(T_obs, clusters, cluster_p_values, t_threshold, min_duration=min_duration, data=data, label=cond,
                            times=times, p_accept=p, fnout=fn_out1)

        
        good_cluster_inds = np.where(cluster_pvalues < p)[0]
        print 'the amount of significant clusters and duration larger than %d ms are: %d' %(min_duration, good_cluster_inds.shape[0])
        clu = list(clu)
        clu[2] = cluster_pvalues
        clu = tuple(clu)
        # Save the clusters as stc file
        np.savez(fn_out, clu=clu, tstep=tstep, fsave_vertices=fsave_vertices)
        assert good_cluster_inds.shape != 0, ('Current p_threshold is %f %p_thr,\
                                    maybe you need to reset a lower p_threshold')



def sample2_clus(fn_list, n_per=8192, pthr=0.01, p=0.05, tail=0, min_duration=20, 
                 del_vers=None, n_jobs=1):
    '''
      Calculate significant clusters using 2 sample ftest.

      Parameter
      ---------
      fn_list: list
        Paths of group arrays
      n_per: int
        The permutation for ttest.
      pct: int or float.
        The percentile of the baseline distribution.
      p: float
        The corrected p_values for comparisons.
      tail: 0 or 1.
        0 stands for 2-tailed test, 1 stands for 1-tailed test.
      min_duration: int or float.
        The minimum duration of significant clusters (ms).
      del_vers: None or _exclu_vers
        If is '_exclu_vers', delete the vertices in the medial wall.
    '''
    for fn_npz in fn_list:
        fn_path = os.path.dirname(fn_npz)
        name = os.path.basename(fn_npz)
        #fn_out = fn_path + '/clu2sample_%s' %name[:name.rfind('.npz')] + '_%d_pct%.2f.npz' %(n_per, pct)
        fn_out = fn_path + '/clu2sample_%s' %name[:name.rfind('.npz')] + '_%d_%dtail_pthr%.7f.npz' %(n_per, 1+(tail==0), pthr)
        npz = np.load(fn_npz)
        tstep = npz['tstep'].flatten()[0]
        #    Note that X needs to be a multi-dimensional array of shape
        #    samples (subjects) x time x space, so we permute dimensions
        X = npz['X']
        times = npz['times'] * 1000 # times in ms
        ppf = stats.f.ppf
        #tail = 1   # tail = we are interested in an increase of variance only
        p_thresh = pthr / (1 + (tail == 0))  # we can also adapt this to p=0.01 if the cluster size is too large
        n_samples_per_group = [len(x) for x in X]
        f_threshold = ppf(1. - p_thresh, *n_samples_per_group)
        if np.sign(tail) < 0:
            f_threshold = -f_threshold
        fsave_vertices = [np.arange(X.shape[-1]/2), np.arange(X.shape[-1]/2)]
        print('Clustering..., with threshold:%.2f' %f_threshold)
        connectivity = spatial_tris_connectivity(grade_to_tris(5))
        T_obs, clusters, cluster_p_values, H0 = clu = \
            spatio_temporal_cluster_test(X, n_permutations=n_per, #step_down_p=0.001,
                                        connectivity=connectivity, n_jobs=n_jobs,
                                        # threshold=t_threshold, stat_fun=stats.ttest_ind)
                                        threshold=f_threshold, spatial_exclude=del_vers, tail=tail)
    
        good_cluster_inds = np.where(cluster_p_values < p)[0]
        print 'the amount of significant clusters are: %d' %good_cluster_inds.shape
        # Record the information of the clusters
        name = os.path.basename(fn_npz).split('_')[-1]
        cond = name[:name.rfind('.npz')]
        fn_out1 = fn_npz[:fn_npz.rfind('.npz')] + ',2sample,clus_info.txt'

        data = np.abs(X[0].mean(axis=0) - X[1].mean(axis=0))   # of shape [n_times, n_vertices]
        cluster_pvalues = cluster_info(T_obs, clusters, cluster_p_values, f_threshold, min_duration=min_duration, data=data, label=cond,
                            times=times, p_accept=p, fnout=fn_out1)

        
        good_cluster_inds = np.where(cluster_pvalues < p)[0]
        print 'the amount of significant clusters and duration larger than %d ms are: %d' %(min_duration, good_cluster_inds.shape)
        clu = list(clu)
        clu[2] = cluster_pvalues
        clu = tuple(clu)
        np.savez(fn_out, clu=clu, tstep=tstep, fsave_vertices=fsave_vertices)
        assert good_cluster_inds.shape != 0, ('Current p_threshold is %f %p_thr,\
                                    maybe you need to reset a lower p_threshold')


def clu2STC(fn_list, p_thre=0.05):
    '''
        Generate STCs from significant clusters

        Parameters
        -------
        fn_list: string
            The paths of significant clusters.
        p_thre: float
            The corrected p_values.
        
    '''
    for fn_cluster in fn_list:
        fn_stc_out = fn_cluster[:fn_cluster.rfind('.npz')] + ',pv_%.3f' % (p_thre)
        npz = np.load(fn_cluster)
        clu = npz['clu']
        good_cluster_inds = np.where(clu[2] < p_thre)[0]
        print 'the amount of significant clusters are: %d' %good_cluster_inds.shape
        fsave_vertices = list(npz['fsave_vertices'])
        tstep = npz['tstep'].flatten()[0]
        stc_all_cluster_vis = summarize_clusters_stc(clu, p_thre, tstep=tstep,
                                                    vertices=fsave_vertices, 
                                                    subject='fsaverage')
        #import pdb
        #pdb.set_trace()
        stc_all_cluster_vis.save(fn_stc_out)
