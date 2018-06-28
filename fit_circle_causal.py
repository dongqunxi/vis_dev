#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 28 06:25:22 2018
the original version of mne.viz.circle plots the lower triangular part of the 
connectivity matrix, if you want to plot the causal 
matrix, please modify the '../mne/viz/circle.py' using the following scripts.

@author: Qunxi Dong <qdong17@asu.edu>
"""



# handle 1D and 2D connectivity information
    if con.ndim == 1:
        if indices is None:
            raise ValueError('indices has to be provided if con.ndim == 1')
    elif con.ndim == 2:
        if con.shape[0] != n_nodes or con.shape[1] != n_nodes:
            raise ValueError('con has to be 1D or a square matrix')
        # we use the lower-triangular part
        #indices = np.tril_indices(n_nodes, -1)
        #con = con[indices]
        indices = np.indices((n_nodes,n_nodes))
        indices=indices.reshape((2,n_nodes*n_nodes))
        con = con.flatten() 
    else:
        raise ValueError('con has to be 1D or a square matrix')