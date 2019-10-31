import numpy as np
from scipy.ndimage.filters import generic_filter

a = np.arange(100, dtype=np.float)
ar = np.reshape(a, (10, 10))

identity = np.ones((3, 3))


def cb(arr):
    print(arr)
    return 0


generic_filter(ar, cb, footprint=identity)
