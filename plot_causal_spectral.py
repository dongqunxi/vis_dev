# -*- coding: utf-8 -*-

import os
import numpy as np
import glob
import matplotlib.pyplot as plt

subjects_dir = os.environ['SUBJECTS_DIR']
fn_cau = subjects_dir + '/fsaverage/stcs/201195/LLst_labels_ts,norm,cau.npy'
fn_surr = subjects_dir + '/fsaverage/stcs/201195/LLst_labels_ts,norm,surrcau.npy'
fn_labels = subjects_dir + '/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
ROIs_labels = np.load(fn_labels)
con = np.load(fn_cau)
surr_subject = np.load(fn_surr)

sfreq = 678.17
nfft = 512
delta_F = sfreq / float(2 * nfft)
freqs_band = (4, 45)
fmin_c, fmax_c = int(freqs_band[0] / delta_F), int(freqs_band[1] / delta_F)
freq = np.linspace(0, sfreq / 2, nfft)
freqs = freq[fmin_c:fmax_c+1]
fmin, fmax = freq[fmin_c], freq[fmax_c+1]
c0 = np.percentile(surr_subject, 99.99, axis=0)
c0 = c0[:6, :6, fmin_c:fmax_c+1]
con = con[:6, :6, fmin_c:fmax_c+1]
n_rows, n_cols = con.shape[:2]
names = ROIs_labels[:6]

fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True)
plt.suptitle('201195_LL')

for i in range(n_rows):
    for j in range(i + 1):
        if i == j:
            axes[i, j].set_axis_off()
            continue

        axes[i, j].plot(freqs, con[i, j, :], 'r')
        axes[j, i].plot(freqs, con[j, i, :], 'r')
        axes[i, j].fill_between(freqs, c0[i, j, :], 0)
        axes[j, i].fill_between(freqs, c0[j, i, :], 0)

        if j == 0:
            axes[i, j].set_ylabel(names[i])
            axes[0, i].set_title(names[i])
        if i == (n_rows - 1):
            axes[i, j].set_xlabel(names[j])
        axes[i, j].set_xlim([fmin, fmax])
        axes[i, j].set_ylim([0, 0.6])
        axes[j, i].set_xticks([8, 13, 18, 30, 45])
        axes[j, i].set_yticks([0, 0.2, 0.4, 0.6])
        axes[j, i].set_xlim([fmin, fmax])

        # Show band limits
        for f in [8, 13, 18, 30, 45]:
            axes[i, j].axvline(f, color='k')
            axes[j, i].axvline(f, color='k')
plt.show()
