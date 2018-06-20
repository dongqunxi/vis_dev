import numpy as np
import math

fn_norm = '/home/uais/LLst_labels_ts.npy'
p_max = 50
X = np.load(fn_norm)

n, m, N = X.shape
print X.shape
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
# import pdb
# pdb.set_trace()
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
