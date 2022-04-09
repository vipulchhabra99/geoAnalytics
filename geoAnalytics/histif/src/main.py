import math
import numpy as np
from time import process_time
import rasterio
from rasterio.plot import show
import global_vars

D = None
tlen = None
d = None
tnot = None

def ackley(inp):

    n = len(inp[0])
    cos_mat = np.sum(np.cos(2 * math.pi * inp), axis = 1)
    sq_matrix = np.sqrt(np.sum(np.square(inp), axis = 1)/n)
    ans = 20 + math.exp(1) - math.exp((1/n)*cos_mat) - (20 * math.exp(-0.2 * sq_matrix))
    return ans

def alpine(inp):

    sin_mat = abs(inp * np.sin(inp) + (0.1 * inp))
    ans = np.sum(sin_mat, axis = 1)
    return ans

def dejong_fun2(inp):

    x = inp[:, 0]
    y = inp[:, 1]

    ans = 100 * ((x**2) - y) ** 2 + (1 - x)**2
    return ans

def dejong_fun3(inp):

    ans = np.sum(np.floor(inp), axis = 1)
    return ans

def dejong_fun4(inp):
    
    Dx = len(inp[1,:])
    tlenx = len(inp[:, 1])

    if(global_vars.D is None or global_vars.D != Dx or global_vars.tlen != tlenx):
        global_vars.D = Dx
        global_vars.tlen = tlenx
        global_vars.d = np.matlib.repmat([i for i in range(1, global_vars.D + 1)], tlen, 1)

    ans = global_vars.d * np.power(inp, 4)
    return sum(global_vars.d, axis = 1)

def linear_dyn(sf):

    if(global_vars.tnot == None):
        global_vars.tnot = process_time()

    return (process_time() - global_vars.tnot) * sf

def linear_dyn_f6(inp):
    
    x = inp[:, 1]
    y = inp[:, 2]

    offset = linear_dyn(0.5)
    x_center = offset
    y_center = offset

    num = np.power(np.sin(np.sqrt(np.power(x-x_center,2)) + np.power(y-y_center,2)), 2) - 0.5
    den = np.power((1.0 + 0.01 * (np.power(x-x_center, 2) + np.power(y - y_center, 2))), 2)

    return 0.5 + np.divide(num, den)


def main_psf(get_coarse1, get_fine1, get_coarse2, para, iter):

    pass

def recommended_params(scaling_factor):
    r_hmx = [np.fix(scaling_factor/2), round(scaling_factor * 2.5)]
    r_hmy = [np.fix(scaling_factor/2), round(scaling_factor * 2.5)]
    r_shx = [-scaling_factor, scaling_factor]
    r_shy = [-scaling_factor, scaling_factor]
    r_rot = [35, 65]

    return [r_hmx, r_hmy, r_shx, r_shy, r_rot]

def main_func(coarse_file_t0, fine_file_t0, coarse_file_t1, params, iters):
    
    get_coarse1 = coarse_file_t0
    get_fine1 = fine_file_t0
    get_coarse2 = coarse_file_t1
    get_iter = iters







    
# def gaussian_func(M, std):
#     Mn = (M - 1)/2
#     n = 