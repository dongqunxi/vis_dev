# -*- coding: utf-8 -*-
"""
Reference
---------
[1] Mingzhou Ding, Yonghong Chen. Granger Causality: Basic Theory and Application
to Neuroscience.Elsevier Science, 7 February 2008.
"""
import scot
import numpy as np
from scipy import linalg
def compute_order(X, m_max):
    """Estimate AR order with BIC
       
    Parameters
    ----------
    X : ndarray, shape (trials, n_channels, n_samples)
    
    m_max : int
        The maximum model order to test
    
    Reference
    ---------
    [1] provides the equation:BIC(m) = 2*log[det(Σ)]+ 2*(p**2)*m*log(N*n*m)/(N*n*m),
    Σ is the noise covariance matrix, p is the channels, N is the trials, n
    is the n_samples, m is model order.
    
    Returns
    -------
    o_m : int
        Estimated order
    bic : ndarray, shape (m_max + 1,)
        The BIC for the orders from 1 to m_max.
    """
    
    N, p, n = X.shape
    bic = []
    for m in range(m_max):
        print (m+1)
        mvar = scot.var.VAR(m+1)
        mvar.fit(X)
        sigma = mvar.rescov
        m_bic = np.log(linalg.det(sigma))
        m_bic += (p ** 2) * m * np.log(N*n) / (N*n)
        bic.append(m_bic)
        print ('model order: %d, BIC value: %.2f' %(m+1, bic[m]))
    #bic = np.array(bic)
    o_m = np.argmin(bic) + 1
    return o_m, bic

fn_norm = '/home/uais/LLst_labels_ts,norm.npy'
X = np.load(fn_norm)
X = X.transpose(2,0,1)
p,bic = compute_order(X, 100)