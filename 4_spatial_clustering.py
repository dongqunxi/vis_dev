import glob,os
from stat_cluster import set_directory
from stat_cluster import find_files
#####################################################
# Aplly spatio-temporal clustering for ROI defintion
#####################################################
''' From here data will be calculated in the source
    space. 
'''


do_make_inve = False # Generate inverse operator
do_inver_ave = False # make STC
do_morph_STC = False # Morph individual STC
do_group_STC = False # Group morphed STC into pre and post-stimuls (events)
do_t_test = False# Spatial clustering
do_2sample = False #2 sample test
do_clu2STC = True# Transfer cluster arrays into STC objects.
ex_medial = True # Take the medial wall vertices into cluster estimation

#The main path for ROI definition
subjects_dir = os.environ['SUBJECTS_DIR']+'/'

# parameter of Inversing and Morphing
#method = 'dSPM'
method = 'MNE'
snr = 3
n_jobs = 2

# The parameters for clusterring test
permutation = 8192
mt = 1 #max_step for spatio-temporal clustering
#permutation = 1000   # testing only
pct = 99.99 # The percentile of baseline STCs distributions
min_duration = 20# The minimum duration of the significant clusters
pthr = 0.0000001 #f-threshold

if method == 'dSPM':
    thr = 5.67#Threshold corresponding 0.0001 interval
elif method == 'MNE':
    thr = 5.67
p_v = 0.01 # comparisons corrected p-value
tail = 0 # 0 for two tails test, 1 for 1 tail test.
############################################
# make inverse operator of filtered evoked 
#------------------------------------------
if do_make_inve:
    from stat_cluster import apply_inverse_ave
    print '>>> Calculate inverse solution ....'
    fn_evt_list = glob.glob(subjects_dir+'*[0-9]/MEG/*bcc,nr,fibp1-45,ar,evt_LLst_bc-ave.fif')
    apply_inverse_ave(fn_evt_list, subjects_dir)
    print '>>> FINISHED with inverse solution.'
    print ''       
        
############################################
# inverse evo to the source space 
#------------------------------------------

if do_inver_ave:
    print '>>> Calculate STC ....'
    from stat_cluster import apply_STC_ave
    fn_evt_list = find_files(subjects_dir, pattern='*bcc,nr,fibp1-45,ar,evt_*_bc-ave.fif') 
    #fn_evt_list = glob.glob(subjects_dir+'*[0-9]/MEG/*bcc,nr,fibp1-45,ar,evt_*_bc-ave.fif')
    apply_STC_ave(fn_evt_list, method=method, snr=snr)
    print '>>> FINISHED with STC generation.'
    print ''
    
    
###################################################
# Morph individual STC into the common brain space 
#--------------------------------------------------
if do_morph_STC:
    print '>>> Calculate morphed STC ....'
    from stat_cluster import morph_STC
    fn_stc_list = glob.glob(subjects_dir+'*[0-9]/MEG/*bcc,nr,fibp1-45,ar,evt_*_bc-lh.stc')
    fn_stc_list = sorted(fn_stc_list)
    morph_STC(fn_stc_list, method, subjects_dir=subjects_dir)
    print '>>> FINISHED with morphed STC generation.'
    print ''

###################################################
# Group STCs into pre- and post-stimulus (events)
#--------------------------------------------------

#The path for storing the results related with ROIs
stcs_path = subjects_dir + 'fsaverage/%s_conf_stc/' %method
set_directory(stcs_path)

if do_group_STC:
    print '>>> Calculate Matrix for contrasts ....'
    from stat_cluster import Ara_norm
    subjects = ['203731', '201195', '203709', '203792', '203969', '203822',
                    '203929', '203867', '203147', '203267', '203840', '203780', '203288']   
    ncond = 8 
    stcs_dir = subjects_dir + 'fsaverage/%s_ROIs' %method
    Ara_norm(subjects, ncond, stcs_dir, stcs_path)
    print '>>> FINISHED with a group matrix generation.'
    print ''

##################################################################
# Spatial clustering for significant clusters related with events
#----------------------------------------------------------------
if do_t_test:
    print '>>> 1sampletest for clustering ....'
    from stat_cluster import sample1_clus, exclu_vers, sample1_clus_thr, sample1_clus_fixed 
    fn_list = glob.glob(stcs_path + 'Group_*.npz')
    fn_list = sorted(fn_list)
    #exclude medial wall vertices or not
    if ex_medial:
        del_vers = exclu_vers(subjects_dir)
    else:
        del_vers = None
        
    sample1_clus(fn_list[1:], n_per=permutation, pct=pct, p=p_v, tail=tail, 
                del_vers=del_vers, min_duration=min_duration, n_jobs=n_jobs)
    #sample1_clus_thr(fn_list[:1], n_per=permutation, pthr=pthr, p=p_v, tail=tail, del_vers=del_vers, n_jobs=n_jobs)
    #sample1_clus_fixed(fn_list, n_per=permutation, thre=thr, p=p_v, tail=tail, max_step=mt, del_vers=del_vers, n_jobs=n_jobs)
    print '>>> FINISHED with the clusters generation.'
    print ''

###############################################################################
# Clustering using 2sample f-test
# -----------------
if do_2sample:
    ''' This comparison is suitable for the samples from different entireties
    '''
    print '>>> 2smpletest for clustering ....'
    permutation2 = permutation / 2
    from stat_cluster import sample2_clus, exclu_vers 
    fn_list = glob.glob(stcs_path + 'Group_*.npz')
    fn_list = sorted(fn_list)
    #exclude medial wall vertices or not
    if ex_medial:
        del_vers = exclu_vers(subjects_dir)
    else:
        del_vers = None
        
    sample2_clus(fn_list, n_per=permutation2, pthr=pthr, p=p_v, del_vers=del_vers, tail=tail)
    print '>>> FINISHED with the clusters generation.'
    print ''
    
###############################################################################
# Transfer significant cluster into STCs
# ----------------------------------------
if do_clu2STC:
    print '>>> Transfer cluster to STC ....'
    from stat_cluster import clu2STC
    #fn_list = glob.glob(stcs_path + 'clu2sample_Group_*_%d_%dtail_pthr%.7f.npz' %(permutation/2, 1+(tail==0), pthr))
    fn_list = glob.glob(stcs_path + 'clu1sample_Group_*_%d_%dtail_pct%.3f_%.1f.npz' %(permutation, 1+(tail==0), pct, min_duration))
    #fn_list = glob.glob(stcs_path + 'clu1sample_Group_*_%d_%dtail_pct%.3f.npz' %(permutation, 1+(tail==0), pct))
    fn_list = sorted(fn_list)
    clu2STC(fn_list, p_thre=p_v)
    
        