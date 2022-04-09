import numpy as np
from scipy.signal import convolve2d
from .psf import PSF
import geoAnalytics.histif.src.global_vars as global_vars
import numpy as np
from scipy.ndimage.filters import convolve

# def conv2(x,y,mode='same'):
#     """
#     Emulate the function conv2 from Mathworks.

#     Usage:

#     z = conv2(x,y,mode='same')

#     TODO: 
#      - Support other modes than 'same' (see conv2.m)
#     """

#     if not(mode == 'same'):
#         raise Exception("Mode not supported")

#     if (len(x.shape) < len(y.shape)):
#         dim = x.shape
#         for i in range(len(x.shape),len(y.shape)):
#             dim = (1,) + dim
#         x = x.reshape(dim)
#     elif (len(y.shape) < len(x.shape)):
#         dim = y.shape
#         for i in range(len(y.shape),len(x.shape)):
#             dim = (1,) + dim
#         y = y.reshape(dim)

#     origin = ()
#     for i in range(len(x.shape)):
#         if ( (x.shape[i] - y.shape[i]) % 2 == 0 and
#              x.shape[i] > 1 and
#              y.shape[i] > 1):
#             origin = origin + (-1,)
#         else:
#             origin = origin + (0,)

#     z = convolve(x,y, mode='constant', origin=origin)

#     return z



#     # Add singleton dimensions
def conv2(x, y, mode='same'):
    return np.rot90(convolve2d(np.rot90(x, 2), np.rot90(y, 2), mode=mode), 2)


def FFT(params, x):
    
    HR = x

    hm_x = params[0]
    hm_y = params[1]
    sh_x = params[2]
    sh_y = params[3]
    angle = params[4]

    psf = PSF(hm_x, hm_y, angle)
    HR_fft = conv2(HR, psf, 'same')
    ends = list(HR_fft.shape)
    HR_fft = HR_fft[int(global_vars.edge + sh_y): int(ends[0] - global_vars.edge + sh_y), int(global_vars.edge + sh_x): int(ends[1]-global_vars.edge + sh_x)]
    HR_p = HR_fft.reshape(1, int(global_vars.N * global_vars.N))

    return HR_p