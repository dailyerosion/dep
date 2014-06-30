import numpy as np
from scipy.ndimage.filters import generic_filter

data = np.arange(100).reshape((10,10))
sz = 3
midpt = 5
identity = np.ones((sz,sz))

def cb(arr):
    # The arr passed here is flattened!
    diff = (np.sum( (arr[midpt] - arr)**2, 0))**.5
    return diff
    
res = generic_filter(data, cb, footprint=identity)

print res