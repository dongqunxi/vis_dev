'''
Display ROIs based on MNE estimates and select dipoles for causality analysis.
'''

import os
import glob
import mne
from surfer import Brain

subjects_dir = '/home/uais_common/dong/freesurfer/subjects/'
stcs_path = subjects_dir + '/fsaverage/conf_stc/'
labels_dir = stcs_path + 'STC_ROI/merge/'

subject_id = 'fsaverage'
hemi = "lh"
# surf = "smoothwm"
surf = 'inflated'
fn_list = glob.glob(labels_dir + '*')
#brain = Brain(subject_id, hemi, surf)
brain = Brain(subject_id, hemi, surf, cortex = 'bone', background='white')
color = ['#990033', '#9900CC', '#FF6600', '#FF3333', '#00CC33']

i = 0
for fn_label in fn_list:
        label_name = os.path.split(fn_label)[-1]
        # if label_name.split('_')[0] == 'sti,RRst':
        i = i + 1
        ind = i % 5
        label = mne.read_label(fn_label)
        if label.hemi == 'lh':
            brain.add_label(label)

brain.add_annotation(annot='aparc', borders=True)
