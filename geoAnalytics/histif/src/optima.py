import numpy as np
from .FFT import FFT
import geoAnalytics.histif.src.global_vars as global_vars

def optima(inputs):
    inputs = np.array(inputs)
    r = np.max(np.array(list(inputs.shape)))

    cost = []
    for i in range(r):
        HR_p = FFT(inputs[i, :], global_vars.HR1)
        cost.append(np.sqrt(np.mean(np.power(HR_p - global_vars.LR1, 2))))

    cost = np.array(cost).T
    HR_pre = HR_p
    return cost, HR_pre