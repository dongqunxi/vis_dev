
import numpy as np
import os, mne
#from dirs_manage import reset_directory, set_directory
subjects_dir = os.environ['SUBJECTS_DIR']
stcs_path = subjects_dir + '/fsaverage/MNE_conf_stc/'             

subject_id = 'fsaverage'

list_file = stcs_path +'func_list.txt'
with open(list_file, 'r') as fl:
            file_list = [line.rstrip('\n') for line in fl]
fl.close()
#i = 0
fn_cor = 'coors.csv'
import csv
fl = open(fn_cor, 'w')
writer = csv.writer(fl)
do_array = True
if do_array:
        #fn_stc = stcs_path + 'Ttestpermu16384_pthr0.0001_res_LLrt,temp_0.001,tmin_0.000-lh.stc' 
        fn_stc = '/home/uais/data/freesurfer/subjects/fsaverage/MNE_ROIs/203731/203731_Chrono01_110518_1636_1_c,rfDC,bcc,nr,fibp1-45,ar,evt_LLrt_bc-lh.stc'
        stc_avg = mne.read_source_estimate(fn_stc)
        #reset_directory(stan_path)
        coors = []
        nalabels = []
        for f in file_list:
            label = mne.read_label(f)
            stc_label = stc_avg.in_label(label)
            stc_label.data[stc_label.data < 0] = 0
            #brain.add_label(label, color='red', alpha=0.5)
            if label.hemi == 'lh':
                vtx, _, _ = stc_label.center_of_mass(subject_id, hemi=0)
                mni_lh = mne.vertex_to_mni(vtx, 0, subject_id)[0]
                #brain.add_foci(vtx, coords_as_verts=True, hemi='lh', color=random.choice(color),
                #                scale_factor=0.8)
                print 'label:%s coordinate: ' %label.name + str(mni_lh)
                mni_lh = np.array(mni_lh)
                mni_lh = list(np.rint(mni_lh))
                irow = mni_lh + [2, 3] + [label.name]    
                writer.writerow(irow)
                
            if label.hemi == 'rh':
                vtx, _, _ = stc_label.center_of_mass(subject_id, hemi=1)
                mni_rh = mne.vertex_to_mni(vtx, 1, subject_id)[0]
                print 'label:%s coordinate: ' %label.name + str(mni_rh)
                mni_rh = np.array(mni_rh)
                mni_rh = list(np.rint(mni_rh))
                irow = mni_rh + [3, 6] + [label.name]    
                writer.writerow(irow)
                
fl.close()
