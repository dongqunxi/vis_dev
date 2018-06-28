#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 16 09:19:44 2018

@author: janeyang1987
"""

"""
=========================================================================
Compute source space connectivity and visualize it using a circular graph
=========================================================================

This example computes the all-to-all connectivity between 68 regions in
source space based on dSPM inverse solutions and a FreeSurfer cortical
parcellation. The connectivity is visualized using a circular graph which
is ordered based on the locations of the regions.
"""
# Authors: Martin Luessi <mluessi@nmr.mgh.harvard.edu>
#          Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Nicolas P. Rougier (graph code borrowed from his matplotlib gallery)
#
# License: BSD (3-clause)

import numpy as np
import matplotlib.pyplot as plt
from mne.viz import circular_layout, plot_connectivity_circle

print(__doc__)
do_vs = False
do_plot = True
do_integ = True
###############################################################################
# Load our data
# -------------
if do_vs:
    i = 0
    n_freq = ['theta','alpha','lowBeta','highBeta','gamma']
    for freq in [(4,8),(8,12),(12,18),(18,30),(30,45)]:
        evt_list = [('LL','LR'),('RR','RL')]
        for evt in evt_list:
            incon = np.load('/Users/janeyang1987/Desktop/ju_plots/plt_circular/npy_folder/norm_%sst_%d_%dHz.npy' %(evt[1],freq[0],freq[1]))
            incon[incon.nonzero()]=2
            con = np.load('/Users/janeyang1987/Desktop/ju_plots/plt_circular/npy_folder/norm_%sst_%d_%dHz.npy' %(evt[0],freq[0],freq[1]))
            sum_con = con + incon
            np.save('/Users/janeyang1987/Desktop/ju_plots/plt_circular/npy_folder/%svs%s_%sHz.npy' %(evt[0],evt[1],n_freq[i]), sum_con)
        i = i + 1

###############################################################################
# Make a connectivity plot
# ------------------------
#
# Now, we visualize this connectivity using a circular graph layout.

# First, we reorder the labels based on their location in the left hemi
if do_plot:
        
    label_names = np.load('/Users/janeyang1987/Desktop/ju_plots/plt_circular/Labels.npy')
    label_names = [name.decode('utf-8') for name in label_names]
    n_freqs = ['theta','alpha','lowBeta','highBeta','gamma']
    #lh_labels = label_names[:12]
    #rh_labels = label_names[12:]
    node_angles = circular_layout(label_names, label_names, start_pos=90,
                                  group_boundaries=[0, len(label_names) / 2])
    
    ii = 1
    for vs in ['LLvsLR', 'RRvsRL']:
        for nf in n_freqs:
            con_cau = np.load('/Users/janeyang1987/Desktop/ju_plots/plt_circular/npy_folder/%s_%sHz.npy' %(vs,nf)) 
            
            if ii < 6:
                fig = plt.figure(num=None, figsize=(10, 10))
                plot_connectivity_circle(con_cau, label_names, n_lines=np.nonzero(con_cau)[0].shape[0],node_edgecolor='black',
                                         node_angles=node_angles, facecolor='white',textcolor='black', colormap='cool',
                                         title=nf, padding=1, fontsize_title=20, fontsize_names=20, colorbar=False, vmin=1, vmax=3, colorbar_pos=(1,0), linewidth=6,
                                         node_width=12, fig=fig)
            else:
                fig = plt.figure(num=None, figsize=(10, 10))
                plot_connectivity_circle(con_cau, label_names, n_lines=np.nonzero(con_cau)[0].shape[0],node_edgecolor='black',
                                         node_angles=node_angles, facecolor='white',textcolor='black',colormap='cool',
                                         title=None, padding=1, fontsize_names=20, colorbar=False, vmin=1, vmax=3, colorbar_pos=(1,0), linewidth=6,
                                         node_width=12, fig=fig)
            plt.tight_layout()
            plt.show()
            fig.savefig('%s_%s.jpg' %(vs,nf), dpi=600, facecolor='white')
            plt.close(fig)
            ii = ii + 1
    
if do_integ:
    from PIL import Image
    def append_images(images, direction='horizontal',
                      bg_color=(255,255,255), aligment='center'):
        """
        Appends images in horizontal/vertical direction.
    
        Args:
            images: List of PIL images
            direction: direction of concatenation, 'horizontal' or 'vertical'
            bg_color: Background color (default: white)
            aligment: alignment mode if images need padding;
               'left', 'right', 'top', 'bottom', or 'center'
    
        Returns:
            Concatenated image as a new PIL image object.
        """
        widths, heights = zip(*(i.size for i in images))
    
        if direction=='horizontal':
            new_width = sum(widths)
            new_height = max(heights)
        else:
            new_width = max(widths)
            new_height = sum(heights)
    
        new_im = Image.new('RGB', (new_width, new_height), color=bg_color)
    
    
        offset = 0
        for im in images:
            if direction=='horizontal':
                y = 0
                if aligment == 'center':
                    y = int((new_height - im.size[1])/2)
                elif aligment == 'bottom':
                    y = new_height - im.size[1]
                new_im.paste(im, (offset, y))
                offset += im.size[0]
            else:
                x = 0
                if aligment == 'center':
                    x = int((new_width - im.size[0])/2)
                elif aligment == 'right':
                    x = new_width - im.size[0]
                new_im.paste(im, (x, offset))
                offset += im.size[1]
    
        return new_im
        
    images1 = list(map(Image.open, ['LLvsLR_theta.jpg', 'LLvsLR_alpha.jpg', 'LLvsLR_lowBeta.jpg', 'LLvsLR_highBeta.jpg', 'LLvsLR_gamma.jpg']))
    images2 = list(map(Image.open, ['RRvsRL_theta.jpg', 'RRvsRL_alpha.jpg', 'RRvsRL_lowBeta.jpg', 'RRvsRL_highBeta.jpg', 'RRvsRL_gamma.jpg']))
    combo_1 = append_images(images1, direction='horizontal')
    combo_2 = append_images(images2, direction='horizontal')
    combo_3 = append_images([combo_1, combo_2], direction='vertical')
    combo_3.save('combo_3.png')
            