import numpy as np
import csv, os
freqs = [(4, 8), (8, 12), (12, 18), (18, 30), (30, 45)]
st_list = ['LLst', 'RRst', 'LRst', 'RLst']
fr_csv = ['theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
for evt in st_list:
    i = 0
    for ifreq in freqs:
        fmin = ifreq[0]
        fmax = ifreq[1] 
        #fn_npy = '/home/uais/data/Chrono/18subjects/fsaverage/causality-GPDC/incon_con_%d-%dHz.npy' %(fmin, fmax)
        fn_npy = '/home/uais/data/freesurfer/subjects/fsaverage/stcs/causality/%s_%d_%dHz.npy' %(evt, fmin, fmax)
        fn_path = os.path.split(fn_npy)[0]
        mat1 = np.load(fn_npy)
        #mat1[mat1==1] = 0.2
        
        csvfile = file(fn_path + '/%s_%s.csv' %(evt, fr_csv[i]), 'wb')
        writer = csv.writer(csvfile)
        writer.writerows(mat1.T)
        csvfile.close()
        i = i + 1
    #fn_npy = '/home/uais/data/Chrono/18subjects/fsaverage/causality-PDC/com_incon_con_%d-%dHz.npy' %(fmin, fmax)
    #mat2 = np.load(fn_npy)
    #mat2[mat2==1] = 0.3
    #
    #
    #
    #fn_npy = '/home/uais/data/Chrono/18subjects/fsaverage/causality-PDC/con_incon_%d-%dHz.npy' %(fmin, fmax)
    #mat3 = np.load(fn_npy)
    #mat3[mat3==1] = 0.1
    #
    #mat = mat1 + mat2 + mat3
    #
    #csvfile = file('%s.csv' %fr_csv[i], 'wb')
    #writer = csv.writer(csvfile)
    ##writer.writerow(np.arange(15))
    #writer.writerows(mat.T)
    #csvfile.close()
    #i = i + 1

#import matplotlib.pylab as plt
#ax = plt.gca()
#ind_mat = np.zeros((7,7))
#ind_mat[0,0],ind_mat[1,2], ind_mat[2,1], ind_mat[3,1], ind_mat[6,1], ind_mat[4,4], ind_mat[5,2], ind_mat[4,3]=1,1,1,1,1,1,1,1
#ind_mat[5,4], ind_mat[6,4], ind_mat[6,5], ind_mat[5,6]=1,1,1,1
#plt.imshow(ind_mat, interpolation='nearest')
#ax.set_xticks(np.arange(7))
#ax.set_xticklabels(['MC-lh', 'SMG-lh', 'PMC-rh', 'SMG-rh', 'DLPFC-rh', 'Insula-rh', 'ACC-rh'])
#ax.set_yticks(np.arange(7))
#ax.set_yticklabels(['DLPFC-lh', 'Insula-lh', 'ACC-lh', 'SMG-rh', 'PMC-rh', 'Insula-rh', 'ACC-rh'])
#for tick in ax.xaxis.get_major_ticks():
#    tick.label1.set_fontsize(10)
#for tick in ax.yaxis.get_major_ticks():
#    tick.label1.set_fontsize(10)
#ax.set_title('incon-con(30-40Hz)')
#