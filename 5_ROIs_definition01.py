'''
ROIs definition using STCs from spatial-temporal clustering.
'''

import os
import numpy as np
import mne
import glob
from apply_merge import apply_merge, redu_small

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

#method = 'dSPM' 
method = 'MNE'               
subjects_dir = os.environ['SUBJECTS_DIR']
stcs_path = subjects_dir + '/fsaverage/%s_conf_stc/' %method# the path of STC
labels_path = stcs_path + 'STC_ROI/' # path where ROIs are saved
fn_src = subjects_dir + '/fsaverage/bem/fsaverage-ico-5-src.fif'
src = mne.read_source_spaces(fn_src)
conditions = ['LLst', 'RRst', 'RLst', 'LRst', 'LLrt', 'RRrt', 'RLrt', 'LRrt']
#fn_stcdata = stcs_path + 'stcsdata.npy'
vert_size = 10 # minimum size for ROIs (mm)

do_ROIs = True
if do_ROIs:
    reset_directory(labels_path+'ini/')
    for cond in conditions:
        #fn_stc = stcs_path + 'clu2sample_Group_%s_4096_2tail_pthr0.0000001,pv_0.010' %(cond)
        fn_stc = stcs_path + 'clu1sample_Group_%s_8192_2tail_pct99.99,pv_0.010-rh.stc' %cond
        stc = mne.read_source_estimate(fn_stc)
        lh_labels, rh_labels = mne.stc_to_label(stc, src=src, smooth=True,
                                        subjects_dir=subjects_dir, connected=True)
        i = 0
        while i < len(lh_labels):
            lh_label = lh_labels[i]
            print 'left hemisphere ROI_%d has %d vertices' %(i, lh_label.vertices.shape[0])
            dist = src[0]['dist']
            label_dist = dist[lh_label.vertices, :][:, lh_label.vertices]
            max_dist = round(label_dist.max() * 1000)
            if max_dist > vert_size:
                lh_label.save(labels_path + 'ini/%s_%s' % (cond, str(i)))
            i = i + 1

        j = 0
        while j < len(rh_labels):
            rh_label = rh_labels[j]
            print 'right hemisphere ROI_%d has %d vertices' % (j, rh_label.vertices.shape[0])
            dist = src[1]['dist']
            label_dist = dist[rh_label.vertices, :][:, rh_label.vertices]
            max_dist = round(label_dist.max() * 1000)
            if max_dist > vert_size:
                rh_label.save(labels_path + 'ini/%s_%s' % (cond, str(j)))
            #rh_label.save(labels_path + 'ini/%s,%s_%s' % (side, conf_type, str(j)))
            j = j + 1

# Merge ROIs across conditions
do_merge = True
if do_merge:
    apply_merge(labels_path)

# Split large cluster
do_split = False
if do_split:
    ''' Before this conduction, we need to check the large ROI which are
        necessary for splitting. Collect the anatomical labels involve in
        the large ROIs. And split them one by one using the following scripts.
    '''
    # The large ROI
    fn_par_list = glob.glob(labels_path + '/merge/*')
    # The corresponding anatomical labels
    #fnana_list = glob.glob(labels_path + '/func_ana/rh/*')
    analabel_list = mne.read_labels_from_annot('fsaverage', subjects_dir=subjects_dir)
    ana_path = labels_path + '/func_ana/'
    reset_directory(ana_path)
    for fn_par in fn_par_list:
        par_label = mne.read_label(fn_par, subject='fsaverage')
        # The path to save splited ROIs
        chis_path = labels_path + '/func_ana/%s/' % par_label.name
        reset_directory(chis_path)
        for ana_label in analabel_list[:-1]:
            #ana_label = mne.read_label(fnana)
            overlapped = len(np.intersect1d(ana_label.vertices,
                                            par_label.vertices))
            if overlapped > 0 and ana_label.hemi == par_label.hemi:  
                chi_label = ana_label - (ana_label - par_label)
                # Only labels larger than vert_size are saved
                if chi_label.hemi == 'lh':
                    h = 0
                else:
                    h = 1
                dist = src[h]['dist']
                label_dist = dist[chi_label.vertices, :][:, chi_label.vertices]
                max_dist = round(label_dist.max() * 1000)
                if max_dist > vert_size:
                    chi_label.save(chis_path+ana_label.name)
                
# Merge ROIs with the same anatomical labels.   
do_merge_ana = False
if do_merge_ana:
    import shutil
    ana_path = glob.glob(labels_path + 'func_ana/*')
    tar_path = labels_path + 'func/'
    reset_directory(tar_path)
    path_list = ana_path[0]
    ana_list = glob.glob(path_list + '/*')
    for filename in ana_list:
        shutil.copy(filename, tar_path)
    for path_list in ana_path[1:]:
        ana_list = glob.glob(path_list + '/*')
        for fn_ana in ana_list:
            ana_label = mne.read_label(fn_ana)
            label_name = ana_label.name
            fn_tar = tar_path + '%s.label' %label_name
            if os.path.isfile(fn_tar):
                tar_label = mne.read_label(fn_tar)
                mer_label = ana_label + tar_label
                os.remove(fn_tar)
                mer_label.save(tar_path + label_name)
                print '%s has %d vertices' %(label_name, mer_label.vertices.shape[0])
            else:
                shutil.copy(fn_ana, tar_path)

#red_size = True
#if red_size:
#    tar_path = labels_path + 'func/'
#    #fn_src = subjects_dir + '/fsaverage/bem/fsaverage-ico-5-src.fif'
#    redu_small(tar_path, vert_size, fn_src)
    
do_write_list = False
if do_write_list:
    tar_path = labels_path + 'func/'
    func_list1 = glob.glob(tar_path + '*-lh.label')
    func_list2 = glob.glob(tar_path + '*-rh.label')
    func_list = func_list1 + func_list2
    fn_func = labels_path + 'func_list.txt'
    text_file = open(fn_func, "w")
    for func in func_list:
        text_file.write("%s\n" %func)
    text_file.close()
