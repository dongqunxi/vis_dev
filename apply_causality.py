import os
import numpy as np
import math
import matplotlib.pylab as plt
import mne
from jumeg.jumeg_preprocessing import get_files_from_list
#from jumeg.jumeg_utils import reset_directory, set_directory
from stat_cluster import reset_directory, set_directory

def apply_inverse_oper(fnepo, tmin=-0.2, tmax=0.8, subjects_dir=None):
    '''
    Apply inverse operator
    Parameter
    ---------
    fnepo: string or list
        The epochs file with ECG, EOG and environmental noise free.
    tmax, tmax:float
        The time period (second) of each epoch.
    '''
    # Get the default subjects_dir
    from mne import make_forward_solution
    from mne.minimum_norm import make_inverse_operator, write_inverse_operator

    fnlist = get_files_from_list(fnepo)
    # loop across all filenames
    for fname in fnlist:
        fn_path = os.path.split(fname)[0]
        name = os.path.basename(fname)
        subject = name.split('_')[0]
        subject_path = subjects_dir + '/%s' % subject
        fn_trans = fn_path + '/%s-trans.fif' % subject
        fn_cov = fn_path + '/%s_empty-cov.fif' % subject
        fn_src = subject_path + '/bem/%s-ico-5-src.fif' % subject
        fn_bem = subject_path + '/bem/%s-5120-5120-5120-bem-sol.fif' % subject
        fn_inv = fn_path + '/%s_epo-inv.fif' % subject

        epochs = mne.read_epochs(fname)
        epochs.crop(tmin, tmax)
        epochs.pick_types(meg=True, ref_meg=False)
        noise_cov = mne.read_cov(fn_cov)
        fwd = make_forward_solution(epochs.info, fn_trans, fn_src, fn_bem)
        fwd['surf_ori'] = True
        inv = make_inverse_operator(epochs.info, fwd, noise_cov, loose=0.2,
                                    depth=0.8, limit_depth_chs=False)
        write_inverse_operator(fn_inv, inv)


def apply_STC_epo(fnepo, event, method='MNE', snr=1.0, min_subject='fsaverage',
                  subjects_dir=None):

    from mne import morph_data
    from mne.minimum_norm import read_inverse_operator, apply_inverse_epochs

    fnlist = get_files_from_list(fnepo)
    # loop across all filenames
    for fname in fnlist:
        fn_path = os.path.split(fname)[0]
        name = os.path.basename(fname)
        subject = name.split('_')[0]
        min_dir = subjects_dir + '/%s' %min_subject
        snr = snr
        lambda2 = 1.0 / snr ** 2
        stcs_path = min_dir + '/stcs/%s/%s/' % (subject,event)
        reset_directory(stcs_path)
        # fn_inv = fname[:fname.rfind('-ave.fif')] + ',ave-inv.fif'
        fn_inv = fn_path + '/%s_epo-inv.fif' %subject

        # noise_cov = mne.read_cov(fn_cov)
        epo = mne.read_epochs(fname)
        epo.pick_types(meg=True, ref_meg=False)
        inv = read_inverse_operator(fn_inv)
        stcs = apply_inverse_epochs(epo, inv, lambda2, method,
                            pick_ori='normal')
        s = 0
        while s < len(stcs):
            stc_morph = morph_data(subject, min_subject, stcs[s])
            stc_morph.save(stcs_path + '/trial%s_fsaverage'
                           % (str(s)), ftype='stc')
            s = s + 1


def cal_labelts(stcs_path, fn_func_list, condition='LLst',
                min_subject='fsaverage', subjects_dir=None):
    '''
    Extract stcs from special ROIs, and store them for funther causality
    analysis.

    Parameter
    ---------
    stcs_path: string
        The path of stc's epochs.
    fn_ana_list: string
        The path of the file including pathes of functional labels.
    condition: string
        The condition for experiments.
    min_subject: the subject for common brain
    '''
    path_list = get_files_from_list(stcs_path)
    minpath = subjects_dir + '/%s' % (min_subject)
    srcpath = minpath + '/bem/fsaverage-ico-5-src.fif'
    src_inv = mne.read_source_spaces(srcpath)
    # loop across all filenames
     # Get common labels
    list_file = fn_func_list
    fn_labels = fn_func_list[:fn_func_list.rfind('.txt')] + '.npy'
    with open(list_file, 'r') as fl:
                file_list = [line.rstrip('\n') for line in fl]
    fl.close()
    rois = []
    labels = []
    for f in file_list:
        label = mne.read_label(f)
        labels.append(label)
        rois.append(label.name)
    rois = np.array(rois)
    np.save(fn_labels, rois)
    
    for stcs_path in path_list:
        caupath = stcs_path[:stcs_path.rfind('/%s' % condition)]
        fn_norm = caupath + '/%s_labels_ts,norm.npy' % (condition)
        #fn_base_stcs = fn_stcs_labels[:fn_stcs_labels.rfind('_label')] + '_baseline.npy'
        _, _, files = os.walk(stcs_path).next()
        trials = len(files) / 2
        # Get unfiltered and morphed stcs
        stcs = []
        bs_stcs = []
        i = 0
        while i < trials:
            fn_stc = stcs_path + 'trial%s_fsaverage' % (str(i))
            stc = mne.read_source_estimate(fn_stc + '-lh.stc',
                                           subject=min_subject)
            bs_stc = stc.copy().crop(stc.times.min(), 0)
            bs_stcs.append(bs_stc.data)
            stcs.append(stc.crop(0, stc.times.max()))
            i = i + 1
       
        # Extract stcs in common labels
     
        label_ts = mne.extract_label_time_course(stcs, labels, src_inv,
                                                 mode='pca_flip')
        # make label_ts's shape as (sources, samples, trials)
        label_ts = np.asarray(label_ts).transpose(1, 2, 0)
        bs_stcs = np.asarray(bs_stcs).transpose(1, 2, 0)
        d_mu = bs_stcs.mean()
        d_std = bs_stcs.std()
        z_data = (label_ts - d_mu) / d_std
        pre_ = fn_norm.split('/')[-2] + '_%s' %fn_norm.split('/')[-1].split('_')[0]
        print '%s, scalar: mean %f, std %s' %(pre_, d_mu, d_std)
        import pdb
        pdb.set_trace()
        #np.save(fn_norm, z_data)




def normalize_data(fn_ts, pre_t=0.2, fs=678.17):
    '''
    Before causal model construction, labelts need to be normalized further:
    Apply Z-scoring to each STC.

    Parameter
    ---------
    fnts: string
        The file name of representative STCs for each ROI.
    pre_t: float (s)
        The end timepoint of baseline
    fs: float
        The sampling rate of signals
 
    '''
    path_list = get_files_from_list(fn_ts)
    # loop across all filenames
    for fnts in path_list:
        fnnorm = fnts[:fnts.rfind('.npz')] + ',norm.npy'
        npz = np.load(fnts)
        ts = npz['X']
        #ts = np.load(fnts)
        d_pre = ts[:, :int(pre_t*fs), :]
        d_pos = ts[:, int(pre_t*fs):, :]
        d_mu = []
        d_std = []
        for d_ in d_pre:
            d_mu.append(d_.mean(keepdims=True))
            d_std.append(d_.std(ddof=1, keepdims=True))
        
        d_mu = np.array(d_mu)
        d_std = np.array(d_std)
        z_data = (d_pos - d_mu) / d_std
        #pre_ = fnnorm.split('/')[-2] + '_%s' %fnnorm.split('/')[-1].split('_')[0]
        np.save(fnnorm, z_data)


def _plot_morder(bics, morder, figmorder):
    '''
    Parameter
    ---------
    bics: array
       BIC values for each model order lower than 'p_max'.
    morder: int
      The optimized model order.
    figmorder: string
      The path for storing the plot.
    '''

    plt.figure()
    
    #h0, = plt.plot(np.arange(len(bic)) + 1, bic, 'r', linewidth=3)
    #plt.legend([h0], ['BIC: %d' % morder])
    plt.plot(np.arange(bics.shape[1]) + 1, bics.T)
    plt.xlabel('order')
    plt.ylabel('BIC')
    plt.title('Model Order: %d' %morder)
    ymin, ymax = plt.ylim()
    plt.vlines(morder, ymin, ymax)
    plt.show()
    plt.savefig(figmorder, dpi=300)
    plt.close()


def model_order(fn_norm, p_max=0, fn_figout=None):
    """
    Calculate the optimized model order for VAR
    models from time series data.

    Parameters
    ----------
    fn_norm: string
        The file name of model order estimation.
    p_max: int
        The upper limit for model order estimation.
    Returns
    ----------
    morder: int
        The optimized BIC model order.
    """
    path_list = get_files_from_list(fn_norm)
    bics = []
    # loop across all filenames
    for fnnorm in path_list:
        X = np.load(fnnorm)
        n, m, N = X.shape
        if p_max == 0:
            p_max = m - 1
        q = p_max
        q1 = q + 1
        XX = np.zeros((n, q1, m + q, N))
        for k in xrange(q1):
            XX[:, k, k:k + m, :] = X
        q1n = q1 * n
        bic = np.empty((q, 1))
        bic.fill(np.nan)
        I = np.identity(n)
        # initialise recursion
        AF = np.zeros((n, q1n))  # forward AR coefficients
        AB = np.zeros((n, q1n))  # backward AR coefficients
        k = 1
        kn = k * n
        M = N * (m - k)
        kf = range(0, kn)
        kb = range(q1n - kn, q1n)
        XF = np.reshape(XX[:, 0:k, k:m, :], (kn, M), order='F')
        XB = np.reshape(XX[:, 0:k, k - 1:m - 1, :], (kn, M), order='F')
        import pdb
        pdb.set_trace()
        CXF = np.linalg.cholesky(XF.dot(XF.T)).T
        CXB = np.linalg.cholesky(XB.dot(XB.T)).T
        AF[:, kf] = np.linalg.solve(CXF.T, I)
        AB[:, kb] = np.linalg.solve(CXB.T, I)
        while k <= q - 1:
            print('model order = %d' % k)
            #import pdb
            #pdb.set_trace()
            tempF = np.reshape(XX[:, 0:k, k:m, :], (kn, M), order='F')
            af = AF[:, kf]
            EF = af.dot(tempF)
            tempB = np.reshape(XX[:, 0:k, k - 1:m - 1, :], (kn, M), order='F')
            ab = AB[:, kb]
            EB = ab.dot(tempB)
            CEF = np.linalg.cholesky(EF.dot(EF.T)).T
            CEB = np.linalg.cholesky(EB.dot(EB.T)).T
            R = np.dot(np.linalg.solve(CEF.T, EF.dot(EB.T)), np.linalg.inv(CEB))
            CRF = np.linalg.cholesky(I - R.dot(R.T)).T
            CRB = np.linalg.cholesky(I - (R.T).dot(R)).T
            k = k + 1
            kn = k * n
            M = N * (m - k)
            kf = np.arange(kn)
            kb = range(q1n - kn, q1n)
            AFPREV = AF[:, kf]
            ABPREV = AB[:, kb]
            AF[:, kf] = np.linalg.solve(CRF.T, AFPREV - R.dot(ABPREV))
            AB[:, kb] = np.linalg.solve(CRB.T, ABPREV - R.T.dot(AFPREV))
            E = np.linalg.solve(AF[:, :n], AF[:, kf]).dot(np.reshape(XX[:, :k, k:m,
                                                          :], (kn, M), order='F'))
            DSIG = np.linalg.det((E.dot(E.T)) / (M - 1))
            i = k - 1
            K = i * n * n
            L = -(M / 2) * math.log(DSIG)
            bic[i - 1] = -2 * L + K * math.log(M)
        # morder = np.nanmin(bic), np.nanargmin(bic) + 1
        morder = np.nanargmin(bic) + 1
        bics.append(bic)
        #figmorder = fnnorm[:fnnorm.rfind('.npz')] + ',morder_%d.png' % morder
        fnnorm_p = fnnorm[:fnnorm.rfind('.npy')] + '.npz' 
        np.savez(fnnorm_p, X=X, morder=morder)
        #return morder
    bics = np.array(bics).squeeze(axis=-1)
    #np.save(fn_figout, bics)
    _plot_morder(bics, morder, fn_figout)
    
def _tsdata_to_var(X,p):
    """
    Calculate coefficients and recovariance and noise covariance of
    the optimized model order.
    ref: http://users.sussex.ac.uk/~lionelb/MVGC/html/tsdata_to_var.html
    Parameters
    ----------
    X: narray, shape (n_sources, n_times, n_epochs)
          The data to estimate the model order for.
    p: int, the optimized model order.
    Returns
    ----------
    A: array, coefficients of the specified model
    SIG:array, recovariance of this model
    E:  array, noise covariance of this model
    """
    n, m, N = X.shape
    p1 = p + 1
    A = np.nan
    SIG = np.nan
    E = np.nan
    q1n = p1 * n
    I = np.eye(n)
    XX = np.zeros((n, p1, m + p, N))
    for k in xrange(p1):
        XX[:, k, k:k + m, :] = X
    AF = np.zeros((n, q1n))
    AB = np.zeros((n, q1n))
    k = 1
    kn = k * n
    M = N * (m - k)
    kf = range(0, kn)
    kb = range(q1n - kn, q1n)
    XF = np.reshape(XX[:, 0:k, k:m, :], (kn, M), order='F')
    XB = np.reshape(XX[:, 0:k, k - 1:m - 1, :], (kn, M), order='F')
    CXF = np.linalg.cholesky(XF.dot(XF.T)).T
    CXB = np.linalg.cholesky(XB.dot(XB.T)).T
    AF[:, kf] = np.linalg.solve(CXF.T, I)
    AB[:, kb] = np.linalg.solve(CXB.T, I)
    while k <= p:
        tempF = np.reshape(XX[:, 0:k, k:m, :], (kn, M), order='F')
        af = AF[:, kf]
        EF = af.dot(tempF)
        tempB = np.reshape(XX[:, 0:k, k - 1:m - 1, :], (kn, M), order='F')
        ab = AB[:, kb]
        EB = ab.dot(tempB)
        CEF = np.linalg.cholesky(EF.dot(EF.T)).T
        CEB = np.linalg.cholesky(EB.dot(EB.T)).T
        R = np.dot(np.linalg.solve(CEF.T, EF.dot(EB.T)), np.linalg.inv(CEB))
        RF = np.linalg.cholesky(I - R.dot(R.T)).T
        RB = np.linalg.cholesky(I - (R.T).dot(R)).T
        k = k + 1
        kn = k * n
        M = N * (m - k)
        kf = np.arange(kn)
        kb = range(q1n - kn, q1n)
        AFPREV = AF[:, kf]
        ABPREV = AB[:, kb]
        AF[:, kf] = np.linalg.solve(RF.T, AFPREV - R.dot(ABPREV))
        AB[:, kb] = np.linalg.solve(RB.T, ABPREV - R.T.dot(AFPREV))
    E = np.linalg.solve(AFPREV[:, :n], EF)
    SIG = (E.dot(E.T)) / (M - 1)
    E = np.reshape(E, (n, m - p, N), order='F')
    temp = np.linalg.solve(-AF[:, :n], AF[:, n:])
    A = np.reshape(temp, (n, n, p), order='F')
    return A, SIG, E


def _erfcc(x):
    """Whiteness test. Complementary error function."""
    z = abs(x)
    t = 1. / (1. + 0.5 * z)
    r = t * math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (.37409196 +
                     t * (.09678418 + t * (-.18628806 + t * (.27886807 +
                     t * (-1.13520398 + t * (1.48851587 + t * (-.82215223 +
                                                               t * .17087277)))))))))
    if (x >= 0.):
        return r
    else:
        return 2. - r


def _normcdf(x, mu, sigma):
    t = x - mu
    y = 0.5 * _erfcc(-t / (sigma * math.sqrt(2.0)))
    if y > 1.0:
        y = 1.0
    return y


def _durbinwatson(X, E):
    n, m = X.shape
    dw = np.sum(np.diff(E, axis=0) ** 2) / np.sum(E ** 2, axis=0)
    A = np.dot(X, X.T)
    from scipy.signal import lfilter
    B = lfilter(np.array([-1, 2, -1]), 1, X.T, axis=0)
    temp = X[:, [0, m - 1]] - X[:, [1, m - 2]]
    B[[0, m - 1], :] = temp.T
    D = np.dot(B, np.linalg.pinv(A))
    C = X.dot(D)
    nu1 = 2 * (m - 1) - np.trace(C)
    nu2 = 2 * (3 * m - 4) - 2 * np.trace(B.T.dot(D)) + np.trace(C.dot(C))
    mu = nu1 / (m - n)
    sigma = math.sqrt(2./((m - n) * (m - n + 2)) * (nu2 - nu1 * mu))
    pval = _normcdf(dw, mu, sigma)
    pval = 2 * min(pval, 1-pval)
    return dw, pval


def _whiteness(X, E):
    """
    Durbin-Watson test for whiteness (no serial correlation) of
    VAR residuals.
    Prarameters
    -----------
    X: array
      Multi-trial time series data.
    E: array
      Residuals time series.

    Returns
    -------
    dw: array
       Vector of Durbin-Watson statistics.
    pval: array
         Vector of p-values.
    """
    n, m, N = X.shape
    dw = np.zeros(n)
    pval = np.zeros(n)
    for i in xrange(n):
        Ei = np.squeeze(E[i, :, :])
        e_a, e_b = Ei.shape
        tempX = np.reshape(X, (n, m * N), order='F')
        tempE = np.reshape(Ei, (e_a * e_b), order='F')
        dw[i], pval[i] = _durbinwatson(tempX, tempE)
    return dw, pval


def _consistency(X, E):
    '''
    Consistency test
    Parameters
    -----------
    X: array
      Multi-trial time series data.
    E: array
      Residuals time series.
    Returns
    -------
    cons: float
    consistency test measurement.
    '''
    n, m, N = X.shape
    p = m - E.shape[1]
    X = X[:, p:m, :]
    n1, m1, N1 = X.shape
    X = np.reshape(X, (n1, m1 * N1), order='F')
    E = np.reshape(E, (n1, m1 * N1), order='F')
    s = N * (m - p)
    Y = X - E
    Rr = X.dot(X.T) / (s - 1)
    Rs = Y.dot(Y.T) / (s - 1)
    cons = 1 - np.linalg.norm(Rs - Rr, 2) / np.linalg.norm(Rr, 2)
    return cons


def model_estimation(fn_norm, fn_eval, thr_cons=0.8, whit_min=1., whit_max=3.,
                     morder=None):
    '''
    Check the statistical evalutions of the MVAR model corresponding the
    optimized morder.
    Reference
    ---------
    Granger Causal Connectivity Analysis: A MATLAB Toolbox, Anil K. Seth
    (2009)
    Parameters
    ----------
    fn_norm: string
        The file name of model order estimation.
    thr_cons:float
        The threshold of consistency evaluation.
    whit_min:float
        The lower limit for whiteness evaluation.
    whit_max:float
        The upper limit for whiteness evaluation.
    p: int
       Optimized model order.
    '''
    import scot
    path_list = get_files_from_list(fn_norm)
    # loop across all filenames
    
    for fnnorm in path_list:
        #fneval = fnnorm[:fnnorm.rfind('.npz')] + '_evaluation.txt'
        pre_ = fnnorm.split('/')[-2] + '_%s' %fnnorm.split('/')[-1].split('_')[0]
        npz = np.load(fnnorm)
        if morder == None:
            morder = npz['morder'].flatten()[0]
            #fneval = fnnorm[:fnnorm.rfind('.npz')] + '_evaluation.txt'
        #else:
            #fneval = fnnorm[:fnnorm.rfind(',morder')] + ',morder_%d_evaluation.txt' % morder
        #X = np.load(fnnorm)
        print '>>> Model order is %d....' % morder
        
        X = npz['X']
        A, SIG, E = _tsdata_to_var(X, morder)
        whi = False
        dw, pval = _whiteness(X, E)
        if np.all(dw < whit_max) and np.all(dw > whit_min):
            whi = True
        #if np.all(pval < 0.05):
         #   whi = True
        cons = _consistency(X, E)
        X = X.transpose(2, 0, 1)
        mvar = scot.var.VAR(morder)
        mvar.fit(X)
        is_st = mvar.is_stable()
        if cons < thr_cons or is_st is False or whi is False:
            print fnnorm
        # assert cons > thr_cons and is_st and whi, ('Consistency, whiteness, stability:\
        #                                    %f, %s, %s' %(cons, str(whi), str(is_st)))
        with open(fn_eval, "a") as f:
            f.write('%s model_order, whiteness, consistency, stability: %d, %s, %f, %s\n'
                    % (pre_, morder, str(whi), cons, str(is_st)))


def _plot_hist(con_b, surr_b, fig_out, pre_):
    '''
     Plot the distribution of real and surrogates' causality results.
     Parameter
     ---------
     con_b: array
            Causality matrix.
     surr_b: array
            Surrogates causality matix.
     fig_out: string
            The path to store this distribution.
    '''
    import matplotlib.pyplot as pl
    fig = pl.figure('Histogram - surrogate vs real')
    c = con_b  # take a representative freq point
    fig.add_subplot(211, title='%s - real connectivity' %pre_)
    pl.hist(c, bins=100)  # plot histogram with 100 bins (representative)
    s = surr_b
    fig.add_subplot(212, title='%s - surrogate connectivity' %pre_)
    pl.hist(s, bins=100)  # plot histogram
    #plt.show()
    pl.savefig(fig_out)
    pl.close(fig)


def _plot_thr(con_b, fdr_thr, max_thr, alpha, fig_out, title):
    '''
    Plot the significant threshold of causality analysis.
    Parameter
    ---------
    con_b: array
        Causality matrix.
    fdr_thr: float
       Threshold combining with FDR.
    max_thr: float
       Threshold from the maximum causality value of surrogates.
    fig_out: string
       The path to store the threshold plots.
    '''
    # plt.ioff()
    #plt.close('all')
    c = np.unique(con_b)
    plt.figure('thre')
    plt.plot(c, 'k', label='real con')
    xmin, xmax = plt.xlim()
    plt.hlines(fdr_thr, xmin, xmax, linestyle='--', colors='k',
               label='per=%.2f:%.2f' % (alpha,fdr_thr), linewidth=2)
               # label='p=%.2f(FDR):%.2f' % (alpha,fdr_thr), linewidth=2)
    plt.hlines(max_thr, xmin, xmax, linestyle='--', colors='g',
               label='Max surr', linewidth=2)
    plt.legend()
    plt.xlabel('points')
    plt.ylabel('causality values')
    plt.title(title)
    # pl.show()
    plt.savefig(fig_out)
    plt.close('thre')
    return

def _plot_spectral(cau, surr, ROIs, sfreq, nfft, freqs, per, title, fn_fig):
    
    delta_F = sfreq / float(2 * nfft)
    freqs_band = (freqs[0][0], freqs[-1][-1])
    fmin_c, fmax_c = int(freqs_band[0] / delta_F), int(freqs_band[1] / delta_F)
    freq = np.linspace(0, sfreq / 2, nfft)
    freqs = freq[fmin_c:fmax_c+1]
    fmin, fmax = freq[fmin_c], freq[fmax_c+1]
    c0 = np.percentile(surr, per, axis=0)
    c0 = c0[ :6, :6, fmin_c:fmax_c+1]
    con = cau[:6, :6, fmin_c:fmax_c+1]
    n_rows, n_cols = con.shape[:2]
    names = ROIs
    bands_b = []
    for b_freq in freqs:
        bands_b.append(b_freq[-1])
        
    plt.figure('spectral1',figsize=(25,25))
    fig, axes = plt.subplots(n_rows, n_cols, sharex=True, sharey=True)
    plt.suptitle(title)
    
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
            axes[i, j].set_ylim([0, 0.4])
            axes[j, i].set_xticks(bands_b)
            axes[j, i].set_yticks([0, 0.2, 0.4])
            axes[j, i].set_xlim([fmin, fmax])
    
            # Show band limits
            for f in bands_b:
                axes[i, j].axvline(f, color='k')
                axes[j, i].axvline(f, color='k')
                
    plt.savefig(fn_fig)          
    plt.close('spectral')
    return
    
    
def causal_analysis(fn_norm, ROIs=None, method='GPDC', morder=None, repeats=1000,
                    msave=False, plt_spectral=True, per=99.99, sfreq=678, ncond=4,
                    freqs=[(4, 8), (8, 12), (12, 18), (18, 30), (30, 45)]):
    '''
    Calculate causality matrices of real data and surrogates. And calculate
    the significant causal matrix for each frequency band.
    Parameters
    ----------
    fnnorm: string
        The file name of model order estimation.
    morder: int
        The optimized model order.
    method: string
        causality measures.
    repeats: int
        Shuffling times for surrogates.
    plt_spectral: bool
        Save the causal spectral matrix.
    msave: bool
        Save the causal matrix of the whole frequency domain or not.
    per: float or int
        Percentile of the surrogates.
    sfreq: float
        The sampling rate.
    freqs: list
        The list of interest frequency bands.
    '''
    import scot.connectivity_statistics as scs
    from scot.connectivity import connectivity
    import scot
    path_list = get_files_from_list(fn_norm)
    # loop across all filenames
    nsubjects = len(path_list)/ncond
    fn_list = np.reshape(path_list,(nsubjects,ncond)) 
    bands = ['theta', 'alpha', 'beta1', 'beta2', 'gamma']
    for isubj in range(nsubjects):
        plt.figure('axes')
        sub_fig = [221, 222, 223, 224]
       
        for icond in range(ncond):
            fnnorm = fn_list[isubj, icond]
            title = fnnorm.split('/')[-2] + '_%s' %fnnorm.split('/')[-1].split('_')[0]
            cau_path = os.path.split(fnnorm)[0]
            name = os.path.basename(fnnorm)
            condition = name.split('_')[0]
            npz = np.load(fnnorm)
            if morder == None:
                morder = npz['morder'].flatten()[0]
                fncau = fnnorm[:fnnorm.rfind('.npz')] + ',cau.npy' 
                fnsurr = fnnorm[:fnnorm.rfind('.npz')] + ',surrcau.npy'
            else:
                fncau = fnnorm[:fnnorm.rfind('.npy')] + ',morder%d,cau.npy' % morder
                fnsurr = fnnorm[:fnnorm.rfind('.npy')] + ',morder%d,surrcau.npy' % morder
            
            sig_path = cau_path + '/sig_cau_%d/' % morder
            set_directory(sig_path)
            
            X = npz['X']
            X = X.transpose(2, 0, 1)
            mvar = scot.var.VAR(morder)
            surr = scs.surrogate_connectivity(method, X, mvar,
                                            repeats=repeats)
            mvar.fit(X)
            cau = connectivity(method, mvar.coef, mvar.rescov)
            nfft = cau.shape[-1]
            delta_F = sfreq / float(2 * nfft)
            
            if plt_spectral:
                fn_fig = fncau[:fncau.rfind('.npy')] + '.png'
                _plot_spectral(cau, surr, ROIs, sfreq, nfft, freqs, per, title, fn_fig)
                import pdb
                pdb.set_trace()
            if msave:
                np.save(fncau, cau)
                np.save(fnsurr, surr)
                import pdb
                pdb.set_trace()
                
            
            sig_freqs = []
            nfreq = len(freqs)
            surr_bands = []
            cau_bands = []
            
            thres = []
            maxes = []
            for ifreq in range(nfreq):
                print 'Frequency index used..', ifreq
                fmin, fmax = int(freqs[ifreq][0] / delta_F), int(freqs[ifreq][1] /
                                                                delta_F)
                con_band = np.mean(cau[:, :, fmin:fmax + 1], axis=-1)
                np.fill_diagonal(con_band, 0)
                surr_band = np.mean(surr[:, :, :, fmin:fmax + 1], axis=-1)
                r, s, _ = surr_band.shape
                for i in xrange(r):
                    ts = surr_band[i]
                    np.fill_diagonal(ts, 0)
                surr_bands.append(surr_band)
                cau_bands.append(con_band)
                con_b = con_band.flatten()
                con_b = con_b[con_b > 0]
                surr_b = surr_band.reshape(r, s * s)
                surr_b = surr_b[surr_b > 0]
                
                thr = np.percentile(surr_band, per)
                max_value = surr_band.max()
                thres.append(thr)
                maxes.append(max_value)
                
                print 'max surrogates %.4f' % thr
                con_band[con_band < thr] = 0
                con_band[con_band >= thr] = 1
                histout = sig_path + '%s,%d-%d,distribution.png'\
                    % (condition, freqs[ifreq][0], freqs[ifreq][1])
                throut = sig_path + '%s,%d-%d,threshold.png'\
                    % (condition, freqs[ifreq][0], freqs[ifreq][1])
                _plot_hist(con_b, surr_b, histout, title + ',%d-%dHz' %(freqs[ifreq][0], freqs[ifreq][1]))
                # _plot_thr(con_b, thr, surr_band.max(), alpha, throut)
                _plot_thr(con_b, thr, max_value, per, throut, title + ',%d-%dHz' %(freqs[ifreq][0], freqs[ifreq][1]))
                sig_freqs.append(con_band)
    
            sig_freqs = np.array(sig_freqs)
            print 'Saving computed arrays..'
            np.save(sig_path + '%s_sig_con_band.npy' % condition, sig_freqs)
            del cau, surr
            
            ax = plt.subplot(sub_fig[icond])
            plt.ylim(0, 0.5)
            ax.set_xlabel('bands')
            ax.set_ylabel('scales')
            plt.title('%s' %fnnorm.split('/')[-1].split('_')[0])
            
            width = 0.35
            index = np.arange(len(thres)) 
            
            plt.bar(index, thres, width, color='blue', label='99.99per')
            i = 0
            for x, y in zip(index, thres): 
                plt.text(x+0.3,y+0.01, '%.2f' %y, ha='center', va='bottom', rotation=90)
                i = i + 1
            
            plt.bar(index+width, maxes, width, color='yellow', label='maxes')
            j = 0
            for x, y in zip(index, maxes): 
                plt.text(x+0.6,y+0.01, '%.2f' %y, ha='center', va='bottom', rotation=90)
                j = j + 1
                
            plt.xticks(index + width, bands)
            plt.legend(loc='upper center', fontsize='x-small')
            #plt.legend(loc='upper left')
        
        plt.suptitle(fnnorm.split('/')[-2])
        plt.tight_layout()
        fn_fig_out = sig_path + '%s_sig_con_band.png' %fnnorm.split('/')[-2]
        plt.savefig(fn_fig_out)
        plt.close('axes')
        #import pdb
        #pdb.set_trace()

    return


def sig_thresh(cau_list, freqs, per=99.99, sfreq=678):
    '''
       Evaluate the significance for each pair's causal interactions.
       Parameter
       ---------
       cau_list: string
            The file path of causality matrices.
       freqs: list
            The list of interest frequency bands.
       sfreq: float
            The sampling rate.
       per: float or int
            Percentile of the surrogates.
    '''
    path_list = get_files_from_list(cau_list)
    # loop across all filenames
    for fncau in path_list:
        fnsurr = fncau[:fncau.rfind(',cau.npy')] + ',surrcau.npy'
        cau_path = os.path.split(fncau)[0]
        name = os.path.basename(fncau)
        condition = name.split('_')[0]
        sig_path = cau_path + '/sig_cau/'
        set_directory(sig_path)
        cau = np.load(fncau)
        surr = np.load(fnsurr)
        nfft = cau.shape[-1]
        delta_F = sfreq / float(2 * nfft)
        
        sig_freqs = []
        nfreq = len(freqs)
        for ifreq in range(nfreq):
            fmin, fmax = int(freqs[ifreq][0] / delta_F), int(freqs[ifreq][1] /
                                                             delta_F)
            con_band = np.mean(cau[:, :, fmin:fmax + 1], axis=-1)
            np.fill_diagonal(con_band, 0)
            surr_band = np.mean(surr[:, :, :, fmin:fmax + 1], axis=-1)
            r, s, _ = surr_band.shape
            for i in xrange(r):
                ts = surr_band[i]
                np.fill_diagonal(ts, 0)
            con_b = con_band.flatten()
            con_b = con_b[con_b > 0]
            surr_b = surr_band.reshape(r, s * s)
            surr_b = surr_b[surr_b > 0]
            thr = np.percentile(surr_band, per)
            print 'max surrogates %.4f' % thr
            con_band[con_band < thr] = 0
            con_band[con_band >= thr] = 1
            histout = sig_path + '%s,%d-%d,distribution.png'\
                                % (condition, freqs[ifreq][0], freqs[ifreq][1])
            throut = sig_path + '%s,%d-%d,threshold.png'\
                        % (condition, freqs[ifreq][0], freqs[ifreq][1])
            _plot_hist(con_b, surr_b, histout)
            #_plot_thr(con_b, thr, surr_band.max(), alpha, throut)
            _plot_thr(con_b, thr, surr_band.max(), per, throut)
            con_band[con_band < thr] = 0
            con_band[con_band >= thr] = 1
            sig_freqs.append(con_band)
        sig_freqs = np.array(sig_freqs)
        np.save(sig_path + '%s_sig_con_band.npy' %condition, sig_freqs)

def common_causality(sig_list, condition, freqs, ROI_labels, out_path, p_val):

    """
    Make group causality analysis, by evaluating significant matrices across
    subjects.
    ----------
    sig_list: list
        The path list of individual significant causal matrix.
    condition: string
        One condition of the experiments.
    freqs: list
        The list of interest frequency band.
    min_subject: string
        The subject for the common brain space.
    submount: int
        Significant interactions come out at least in 'submount' subjects.
    """
    from scipy.stats import ttest_1samp
    print 'Running group causality...'
    set_directory(out_path)
    sig_caus = []

    for f in sig_list:
        sig_cau = np.load(f)
        print sig_cau.shape[-1]
        sig_caus.append(sig_cau)

    sig_caus = np.array(sig_caus)
    for ifreq in xrange(len(freqs)):
        b_caus = sig_caus[:, ifreq, :, :]
        subjs, ns = b_caus.shape[:2]
        b_caus = b_caus.reshape(subjs, ns*ns)
        popmean = 0#expected value in null hypothesis
        t_,p_ = ttest_1samp(b_caus,popmean)
        #set nonsignificant values as 0
        #set significant values as 1
        p_[p_>p_val]=0
        p_[p_>0] = 1
        com_con = p_.reshape(ns,ns)
    return

def group_causality(sig_list, condition, freqs, ROI_labels, out_path=None, submount=10):

    """
    Make group causality analysis, by evaluating significant matrices across
    subjects.
    ----------
    sig_list: list
        The path list of individual significant causal matrix.
    condition: string
        One condition of the experiments.
    freqs: list
        The list of interest frequency band.
    min_subject: string
        The subject for the common brain space.
    submount: int
        Significant interactions come out at least in 'submount' subjects.
    """
    print 'Running group causality...'
    set_directory(out_path)
    sig_caus = []

    for f in sig_list:
        sig_cau = np.load(f)
        print sig_cau.shape[-1]
        sig_caus.append(sig_cau)

    sig_caus = np.array(sig_caus)
    sig_group = sig_caus.sum(axis=0)
    plt.close()
    for i in xrange(len(sig_group)):
        fmin, fmax = freqs[i][0], freqs[i][1]
        cau_band = sig_group[i]
        # cau_band[cau_band < submount] = 0
        cau_band[cau_band < submount] = 0
        # fig, ax = pl.subplots()
        cmap = plt.get_cmap('hot', cau_band.max()+1-submount)
        cmap.set_under('gray')
        plt.matshow(cau_band, interpolation='nearest', vmin=submount, cmap=cmap)
        plt.xticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=9, rotation='vertical')
        plt.yticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=9)
        # pl.imshow(cau_band, interpolation='nearest')
        # pl.set_cmap('BlueRedAlpha')
        np.save(out_path + '/%s_%s_%sHz.npy' %
                (condition, str(fmin), str(fmax)), cau_band)
        v = np.arange(submount, cau_band.max()+1, 1)

        # cax = ax.scatter(x, y, c=z, s=100, cmap=cmap, vmin=10, vmax=z.max())
        # fig.colorbar(extend='min')

        plt.colorbar(ticks=v, extend='min')
        # pl.show()
        plt.xlabel('%s_%s_%sHz.png' %(condition, str(fmin), str(fmax)))
        #plt.tight_layout()
        plt.savefig(out_path + '/%s_%s_%sHz.png' %
                    (condition, str(fmin), str(fmax)), dpi=300)
        plt.close()
    return

class ImageFollower(object):
    'update image in response to changes in clim or cmap on another image'

    def __init__(self, follower):
        self.follower = follower

    def __call__(self, leader):
        self.follower.set_cmap(leader.get_cmap())
        self.follower.set_clim(leader.get_clim())
        

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
        fig_fobj = cau_path + '/conditions4_%d_%dHz.tiff' % (fmin, fmax)
        fig = plt.figure('axes4', dpi=1000)
        sub_fig = [221, 222, 223, 224]
        images = []
        # cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
        for icond in range(len(sub_fig)):
            X = np.load(cau_path + '/%s_%d_%dHz.npy' % (st_list[icond], fmin, fmax))
            ax = plt.subplot(sub_fig[icond])
            title = st_list[icond]
            cmap = plt.get_cmap('hot', X.max()+1-submount)
            cmap.set_under('gray')
            ax_im = ax.matshow(X, interpolation='nearest', vmin=submount, cmap=cmap)
            images.append(ax_im)
            plt.xticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=5, rotation='vertical')
            plt.yticks(np.arange(len(ROI_labels)), ROI_labels, fontsize=5)
            
            ax.grid(False)
            ax.set_xlabel(title)
        plt.suptitle('%d-%dHz' %(fmin,fmax))    
        norm = mpl.colors.Normalize(11, 14)
        cax = fig.add_axes([0.2, 0.00, 0.6, 0.02])
        for i, im in enumerate(images):
            im.set_norm(norm)
            if i > 0:
                images[0].callbacksSM.connect('changed', ImageFollower(im))
        fig.colorbar(images[0], cax, orientation='horizontal')
        plt.tight_layout()
        plt.savefig(fig_fobj)
        plt.close('axes4')


def diff_mat(fmin, fmax, mat_dir=None, ROI_labels=None,
             incon_event=['LRst', 'RLst'], con_event=['LLst', 'RRst']):
    """
    Make comparisons between two conditions' group causal matrices
    ----------
    con_event: list
        The list of congruent conditions.
    incon_event: string
        The name of incongruent condition.
    ROI_labels: list
        The list of ROIs.
    fmin, fmax:int
        The interest bandwidth.
    min_subject: string
        The subject for the common brain space.
    """

    fn_con1 = mat_dir + '/%s_%d_%dHz.npy' % (con_event[0], fmin, fmax)
    fn_con2 = mat_dir + '/%s_%d_%dHz.npy' % (con_event[1], fmin, fmax)
    fn_incon1 = mat_dir + '/%s_%d_%dHz.npy' % (incon_event[0], fmin, fmax)
    fn_incon2 = mat_dir + '/%s_%d_%dHz.npy' % (incon_event[1], fmin, fmax)
    am_ROI = len(ROI_labels)
    con_cau1 = np.load(fn_con1)
    con_cau2 = np.load(fn_con2)
    con_cau = con_cau1 + con_cau2
    incon_cau = np.load(fn_incon1) + np.load(fn_incon2)
    con_cau[con_cau > 0] = 1
    incon_cau[incon_cau > 0] = 1
    dif_cau = incon_cau - con_cau
    dif_cau[dif_cau < 0] = 0
    com_cau = incon_cau - dif_cau
    com_cau[com_cau < 0] = 0
    fn_dif = mat_dir + '/incon_con_%d-%dHz.npy' % (fmin, fmax)
    fn_com = mat_dir + '/com_incon_con_%d-%dHz.npy' % (fmin, fmax)
    fig_dif = mat_dir + '/incon_con_%d-%dHz.png' % (fmin, fmax)
    plt.matshow(dif_cau, interpolation='nearest')
    plt.xticks(np.arange(am_ROI), ROI_labels, fontsize=9, rotation='vertical')
    plt.yticks(np.arange(am_ROI), ROI_labels, fontsize=9)
    plt.xlabel('incon - con_%d-%dHz' % (fmin, fmax))
    #plt.tight_layout()
    # pl.show()
    plt.savefig(fig_dif, dpi=300)
    plt.close()
    np.save(fn_dif, dif_cau)
    np.save(fn_com, com_cau)
    #  print len(np.argwhere(dif_cau))
