'''
Display ROIs based on MNE estimates and select dipoles for causality analysis.
'''

import os
import glob
import mne
from surfer import Brain

#method = 'MNE'
method = 'dSPM'
subject_id = 'fsaverage'
surf = 'inflated'

subjects_dir = os.environ['SUBJECTS_DIR']
stcs_path = subjects_dir + '/fsaverage/%s_conf_stc/' %method
labels_dir = stcs_path + 'STC_ROI/merge/'

hs = ['lh', 'rh']
fn_list = glob.glob(labels_dir + '*')
for h in hs:
# surf = "smoothwm"
    brain = Brain(subject_id, h, surf)
    for fn_label in fn_list:
            label_name = os.path.split(fn_label)[-1]
            # if label_name.split('_')[0] == 'sti,RRst':
            label = mne.read_label(fn_label)
            if label.hemi == h:
                print label
                brain.add_label(label)
    
    brain.add_annotation(annot='aparc', borders=True)
    brain.save_imageset(stcs_path + 'STC_ROI/%scoor_' %h, views=['lateral', 'ventral', 'medial'], filetype='jpg', row=0, col=0)
    brain.close()

import numpy as np
import PIL
from PIL import Image
imgs_dir = stcs_path + 'STC_ROI/'
fn_out = imgs_dir + 'both_hemis.jpg'
list_im1 = glob.glob(imgs_dir + 'lhcoor*.jpg')
list_im2 = glob.glob(imgs_dir + 'rhcoor*.jpg')
list_im1 = sorted(list_im1)
list_im2 = sorted(list_im2)
#list_im1 = glob.glob(imgs_dir + '/lh*.jpg')
#list_im2 = glob.glob(imgs_dir + '/rh*.jpg')
list_ims = [list_im1, list_im2]

#list_im = ['Test1.jpg', 'Test2.jpg', 'Test3.jpg']
imgs_combs = []
for list_im in list_ims:
    images = map(Image.open, list_im)
    widths, heights = zip(*(i.size for i in images))
    
    total_width = sum(widths)
    max_height = max(heights)
    
    new_im = Image.new('RGB', (total_width, max_height))
    
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset,0))
        x_offset += im.size[0]
    
    imgs_combs.append(new_im)
#imgs_comb.save( 'Trifecta.jpg' )    

# for a vertical stacking it is simple: use vstack
min_shape = sorted( [(np.sum(i.size), i.size ) for i in imgs_combs])[0][1]
imgs_sum = np.vstack( (np.asarray( i.resize(min_shape) ) for i in imgs_combs ) )
imgs_sum = PIL.Image.fromarray(imgs_sum)
imgs_sum.save(fn_out)
list_im = list_im1 + list_im2
for fn_im in list_im:
    os.remove(fn_im)