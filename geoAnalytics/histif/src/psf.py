import math
import numpy as np
from numpy.core.fromnumeric import reshape
from scipy.ndimage import rotate
from .gaussian import gaussian

def PSF(hm_x, hm_y, angle):

    sd_x = hm_x / (2 * math.sqrt(2 * math.log(2)))
    sd_y = hm_y / (2 * math.sqrt(2 * math.log(2)))

    x_max = hm_x * 2
    y_max = hm_y * 2

    g_x = gaussian(x_max + 1, sd_x)
    g_y = gaussian(y_max + 1, sd_y)

    # g_y = g_y.reshape(-1, 1)
    # # g_y = np.tile(g_y, len(g_x))
    # # g_xy = (g_y @ g_x)

    g_xy = []
    for i in range(g_y.shape[0]):
        g_xy.append(g_y[i] * g_x)
    # g_xy = g_y.T * g_x
    g_xy = np.array(g_xy)
    # gg = np.linalg.solve(np.array([[np.sum(g_xy)]]).conj().T, g_xy.conj().T).conj().T
    # gg = np.dot(g_xy, np.linalg.pinv(np.array([[np.sum(g_xy)]])))

    gg = g_xy / np.sum(g_xy)

    gg = np.nan_to_num(gg)
    
    mask_r = np.zeros_like(gg)
    mask_r[int(hm_y/2) : int(y_max-(hm_y/2)) + 1, int(hm_x/2):int(x_max-(hm_x/2))+1] = 1
    mask_rot = rotate( mask_r, 360 - angle, reshape = False)
    gg = rotate( gg, 360 - angle, reshape = False)
    gg[np.where(mask_rot == 0)] = 0
    rowpix, colpix = np.where(mask_rot > 0)
    psf = gg[np.min(rowpix):np.max(rowpix), np.min(colpix):np.max(colpix) + 1]
    psf = psf / np.sum(psf)
    return psf


if __name__ == '__main__':
    test = PSF(0, 0, 55)
