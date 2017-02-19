from matplotlib.backends.backend_pdf import PdfPages
import os, glob
from PIL import Image

subjects_dir = os.environ['SUBJECTS_DIR']
path_fig = subjects_dir + '/fsaverage/stcs/'
bands = [('4-8', 'theta'), ('8-12', 'alpha'), ('12-18', 'beta1'), ('18-30', 'beta2'), 
         ('30-40', 'gamma')]
conds = ['LL', 'RR', 'LR', 'RL']
for i in range(bands):
    band_num, band_name = bands[i][0], bands[i][1]
    fn_pdf1 = path_fig + '%s_surrogates_distribution.pdf' %band_name# the file to store figures
    fn_pdf2 = path_fig + '%s_significant_threshold.pdf' %band_name# the file to store figures
    pp1 = PdfPages(fn_pdf1)
    pp2 = PdfPages(fn_pdf2)
    for cond in conds:
        fnfig_list = glob.glob(path_fig + '/*[0-9]/sig_cau_21/%s*%s,distr*' %(cond, band_num))
        fnfig_list = sorted(fnfig_list)
        for fn_fig in fnfig_list:
            fn_fig2 = fn_fig[:fn_fig.rfind(',distribution.png')] + ',threshold.png' 
            fig1 = Image.open(fn_fig)
            fig2 = Image.open(fn_fig2)
            pp1.savefig(fig1)
            pp2.savefig(fig2)
    pp1.close()
    pp2.close()