import math
import numpy as np

def gaussian(M, std):
    Mn = (M - 1)/2
    n = np.array([i for i in range(-int(Mn), int(Mn) + 1, 1)])
    gwin = np.exp(-0.5*np.power((n/std), 2))
    return gwin