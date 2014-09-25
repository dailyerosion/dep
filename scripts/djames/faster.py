import numpy as np
from scipy.ndimage.filters import generic_filter

def calc_slope(arr):
    ''' Array passed here is flattened (1-D) '''
    dx = (arr[1] - arr[0]) / 10.  # TODO: use actual distance
    dy = (arr[2] - arr[1]) / 10.  # TODO: use actual distance
   
    return (dx**2 + dy**2)**0.5 

def corners(arr):
    ''' Modify a 2-D array to all zeros and then set the corners to 1 '''
    arr[:] = 0.
    arr[0,0] = 1.
    arr[-1,0] = 1.
    arr[-1,-1] = 1.
    arr[0,-1] = 1.
    return arr

dem = np.load('testN.npy')
# Initialize output arrays with default value of -9999
slp = np.ones( np.shape(dem), np.float32) * -9999
rng = np.ones( np.shape(dem), np.float32) * -9999

# Compute neighborhood average over 9x9 then 7x7 then 3x3 array
identity = np.ones((9,9))
x9avg = generic_filter(dem, np.average, footprint=identity)
x9 = 100.0 * ((x9avg - dem) / x9avg)
# Compute the slope value by modifying the identity array to only sample
# the corners
x9slp = generic_filter(dem, calc_slope, footprint=corners(identity))

identity = np.ones((7,7))
x7avg = generic_filter(dem, np.average, footprint=identity)
x7 = 100.0 * ((x7avg - dem) / x7avg)
x7slp = generic_filter(dem, calc_slope, footprint=corners(identity))

identity = np.ones((3,3))
x3avg = generic_filter(dem, np.average, footprint=identity)
x3 = 100.0 * ((x3avg - dem) / x3avg)
x3slp = generic_filter(dem, calc_slope, footprint=corners(identity))

# When our x9 value is good and rng has yet to be set, then set it to 9, else
# keep it as rng
rng = np.where( np.logical_and( x9 >= -0.03 , x9 <= 0.03, rng < -999 ), 9, rng)
# same test for the slope value
slp = np.where( np.logical_and( x9 >= -0.03 , x9 <= 0.03, slp < -999 ), 
                x9slp, slp)
rng = np.where( np.logical_and( x7 >= -0.03 , x7 <= 0.03, rng < -999 ), 7, rng)
slp = np.where( np.logical_and( x7 >= -0.03 , x7 <= 0.03, slp < -999 ), 
                x7slp, slp)
rng = np.where( np.logical_and( x3 >= -0.03 , x3 <= 0.03, rng < -999 ), 3, rng)
slp = np.where( np.logical_and( x3 >= -0.03 , x3 <= 0.03, slp < -999 ), 
                x3slp, slp)
