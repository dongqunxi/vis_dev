#from matplotlib.backends.backend_pdf import PdfPages
import os, glob
#from PIL import Image
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

subjects_dir = os.environ['SUBJECTS_DIR']
path_fig = subjects_dir + '/fsaverage/stcs/'
bands = [('4-8', 'theta'), ('8-12', 'alpha'), ('12-18', 'beta1'), ('18-30', 'beta2'), 
         ('30-40', 'gamma')]
conds = ['LL', 'RR', 'LR', 'RL']
for i in range(len(bands)):
    band_num, band_name = bands[i][0], bands[i][1]
    fn_pdf1 = path_fig + '%s_surrogates_distribution.pdf' %band_name# the file to store figures
    fn_pdf2 = path_fig + '%s_significant_threshold.pdf' %band_name# the file to store figures
    c1 = Canvas(fn_pdf1)
    c2 = Canvas(fn_pdf2)
    #pp1 = PdfPages(fn_pdf1)
    #pp2 = PdfPages(fn_pdf2)
    for cond in conds:
        fnfig_list = glob.glob(path_fig + '/*[0-9]/sig_cau_21/%s*%s,distr*' %(cond, band_num))
        fnfig_list = sorted(fnfig_list)
        for fn_fig1 in fnfig_list:
            fn_fig2 = fn_fig1[:fn_fig1.rfind(',distribution.png')] + ',threshold.png' 
            im1 = ImageReader(fn_fig1)
            im2 = ImageReader(fn_fig2)
            imagesize1 = im1.getSize()
            imagesize2 = im2.getSize()
            c1.setPageSize(imagesize1)
            c2.setPageSize(imagesize2)
            c1.drawImage(fn_fig1, 0, 0)
            c2.drawImage(fn_fig2, 0, 0)
            c1.showPage()
            c2.showPage()
            c1.save()
            c2.save()
            #fig1 = Image.open(fn_fig)
            #fig2 = Image.open(fn_fig2)
            #pp1.savefig(fig1)
            #pp2.savefig(fig2)
