import matplotlib.pylab as plt
import numpy as np

        

def plt_conditions(cau_path, st_list, ROI_labels, submount, nfreqs=[(4, 8), (8, 12), (12, 18), (18, 30), (30,45)]):

    '''
    Plot the causal matrix of each frequency band

    Parameter
    ---------
    cau_path: string
        The path to store the significant causal matrix.
    st_list: list
        The name of conditions.
    nfreqs: list
        The frequency bands.
    am_ROI: int
        The amount of ROIs
    '''

    #lbls = np.arange(am_ROI) + 1
    import matplotlib as mpl
    for ifreq in nfreqs:
        fmin, fmax = ifreq[0], ifreq[1]
        fig_fobj = cau_path + '/conditions4_%d_%dHz.jpg' % (fmin, fmax)
        fig = plt.figure('axes4', dpi=300)
        sub_fig = [221, 222, 223, 224]
        images = []
        # cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
        for icond in range(len(sub_fig)):
            X = np.load(cau_path + '/%s_%d_%dHz.npy' % (st_list[icond], fmin, fmax))
            ax = fig.add_subplot(sub_fig[icond])
            title = st_list[icond]
            cmap = plt.get_cmap('YlOrBr')
            cmap.set_under('white')
            cax = ax.matshow(X, interpolation='nearest', vmin=submount, cmap=cmap)
            v = np.arange(submount, X.max()+1, 1)
            fig.colorbar(cax, ticks=v)
            plt.xticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=5, rotation='vertical')
            plt.yticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=5)
            #ax.grid(False)
            ax.set_xlabel(title)
        plt.suptitle('%d-%dHz' %(fmin,fmax))    
        
        plt.tight_layout()
        plt.savefig(fig_fobj)
        plt.close('axes4')
import os
subjects_dir = os.environ['SUBJECTS_DIR']
cau_path = subjects_dir+'/fsaverage/stcs'        
out_path = cau_path + '/causality'
fn_labels = subjects_dir+'/fsaverage/MNE_conf_stc/STC_ROI/func_list.npy'
st_list = ['LLst', 'RRst', 'RLst',  'LRst']
ROIs_labels = np.load(fn_labels)
plt_conditions(out_path, st_list, ROIs_labels, 9)

#gs -sDEVICE=pdfwrite -dNOPAUSE -dBATCH -dSAFER -sOutputFile=sin_800.pdf conditions4_4_8Hz.eps conditions4_8_12Hz.eps conditions4_12_18Hz.eps conditions4_18_30Hz.eps conditions4_30_45Hz.eps