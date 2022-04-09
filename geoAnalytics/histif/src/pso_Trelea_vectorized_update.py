import random
import time
import numpy as np
from .normat import *
from .optima import *

def pso_Trelea_vectorized_update(functname, D, varagin):

    random.seed(5)

    if((functname == None or D == None) and len(varagin) == 0):
        raise Exception("Insufficient Number of Arguments !")
    
    elif(len(varagin) == 0):
        VRmin=np.ones((D,1))*-100
        VRmax=np.ones((D,1))*100
        VR=np.array([VRmin,VRmax])
        minmax = 0
        P = []
        mv = 4
        plotfcn='goplotpso'

    elif(len(varagin) == 1):
        VRmin=np.ones((D,1))*-100
        VRmax=np.ones((D,1))*100
        VR=np.array([VRmin,VRmax])
        minmax = 0
        mv = varagin[0]
        if(mv == None):
            mv = 4
        P = []
        plotfcn='goplotpso'

    elif(len(varagin) == 2):
        mv = varagin[0]
        if(mv == None):
            mv = 4
        VR = varagin[1]
        minmax = 0
        P = []
        plotfcn='goplotpso'

    elif(len(varagin) == 3):
        mv = varagin[0]
        if(mv == None):
            mv = 4
        VR = varagin[1]
        minmax = varagin[2]
        P = []
        plotfcn='goplotpso'

    elif(len(varagin) == 4):
        mv = varagin[0]
        if(mv == None):
            mv = 4
        VR = varagin[1]
        minmax = varagin[2]
        P = varagin[3]
        plotfcn='goplotpso'

    elif(len(varagin) == 5):
        mv = varagin[0]
        if(mv == None):
            mv = 4
        VR = varagin[1]
        minmax = varagin[2]
        P = varagin[3]
        plotfcn=varagin[4]

    elif(len(varagin) == 6):
        mv = varagin[0]
        if(mv == None):
            mv = 4
        VR = varagin[1]
        minmax = varagin[2]
        P = varagin[3]
        plotfcn=varagin[4]
        PSOseedValue = varagin[5]
    
    else:
        raise Exception("Invalid Set of Arguments!")

    Pdef = [100, 200, 24, 2, 2, 0.9, 0.4, 1500, 1e-25, 250, None, 0, 0]
    Plen = len(P)
    
    if(Plen < len(Pdef)):
        for i in range(Plen, len(Pdef)):
            P.append(Pdef[i])


    df = P[0]
    me = P[1]
    ps = P[2]
    ac1 = P[3]
    ac2 = P[4]
    iw1 = P[5]
    iw2 = P[6]
    iwe = P[7]
    ergrd = P[8]
    ergrdep = P[9]
    errgoal = P[10]
    trelea = P[11]
    PSOseed = P[12]

    if(functname == 'pso_neteval'):
        #TODO: Complete this evalin part
        pass

    if(minmax == 2 and errgoal is None):
        raise Exception('minmax= 2, errgoal= NaN: choose an error goal or set minmax to 0 or 1')

    if(PSOseed == 1 and PSOseedValue is None):
        raise Exception('PSOseed flag set but no PSOseedValue was input')

    if(PSOseedValue is not None):
        
        if(D < np.size(PSOseedValue, 1)):
            raise Exception('PSOseedValue column size must be D or less')

        if(ps < np.size(PSOseedValue, 0)):
            raise Exception('PSOseedValue row length must be # of particles or less')

    if(P[0] != 0):
        plotflg = 1

    else:
        plotflg = 0

    tr = np.empty((1, me)) * np.nan

    if(len(mv) == 1):
        velmaskmin = -mv * np.ones((ps, D))
        velmaskmax = mv * np.ones((ps, D))

    elif(len(mv) == D):
        velmaskmin = np.tile(-np.array(mv).transpose(), (ps, 1))
        velmaskmax = np.tile(np.array(mv).transpose(), (ps, 1))

    else:
        raise Exception('Max vel must be either a scalar or same length as prob dimension D')

    min_r_temp = VR[:D, 0]
    max_r_temp = VR[:D, 1]
    posmaskmin = np.tile(min_r_temp.transpose(), (ps, 1))
    posmaskmax = np.tile(max_r_temp.transpose(), (ps, 1))
    posmaskmeth = 3
    
    temp_ans = np.array(normat(np.random.uniform(size = (ps, D), low = 0, high = 1), VR.T, 1))[:ps, :D]
    pos = np.rint(temp_ans)
    for i in range(len(pos[-1])):
        if(pos[-1][i] == 0):
            pos[-1][i] = 1

    if(PSOseed == 1):
        tmpsz = list(PSOseedValue.shape)
        pos[:tmpsz[0], :tmpsz[1]] = PSOseedValue

    testing_var = np.column_stack((forcecol(-np.array(mv)), forcecol(np.array(mv))))
    vel = normat(np.random.rand(ps, D), np.array(testing_var).T, 1)
    pbest = pos

    [out, pre] = optima(pos)
    pbestval = out

    if(minmax == 1):
        idx1 = np.argmax(pbestval)
        gbestval = pbestval[idx1]

    elif minmax == 0:
        idx1 = np.argmin(pbestval)
        gbestval = pbestval[idx1]

    elif(minmax == 2):
        temp_vector = np.power((pbestval - np.ones_like(pbestval) * errgoal), 2)
        temp, idx1 = temp_vector.min(axis = 1)
        gbestval = pbestval[idx1]


    bestpos = np.empty((me, D + 1))
    gbest = pbest[idx1, :]

    bestpos[0, 0:D] = gbest
    sentryval = gbestval
    sentry = gbest

    if(trelea == 3):
        
        kappa = 1
        if((ac1 + ac2) <= 4):
            chi = kappa

        else:
            psi = ac1 + ac2
            chi_den = np.abs(2 - psi - np.sqrt(psi ^ 2 - 4 * psi))
            chi_num = 2 * kappa
            chi = chi_num/chi_den

    rstflg = 0
    cnt = 0
    cnt2 = 0
    iwt = [iw1]

    #final epoch loop
    for i in range(me):
        out, _ = np.array(optima(np.concatenate((pos, gbest.reshape(1, -1)))))
        out = out.reshape(-1, 1)
        outbestval = out[-1, :]
        out = out[:-1, :]
        tr[0, i] = gbestval
        te = i
        bestpos[i,0:D + 1] = np.concatenate((gbest.reshape(1, -1), np.array([gbestval]).reshape(1, 1)), axis=1)

        #plotflg missing

        chkdyn = 1
        rstflg = 0

        if(chkdyn == 1):
            threshld = 0.05
            letiter = 5
            outorng = abs(1 - (outbestval/gbestval)) >= threshld
            samepos = np.any(sentry == gbest)

            if((outorng and samepos) and i%letiter == 0):
                rstflg = 1
                pbest = pos
                pbestval = out
                vel = vel * 10

                if(minmax == 1):
                    idx1 = np.argmax(pbestval)
                    gbestval = pbestval[idx1]
                
                elif(minmax == 0):
                    idx1 = np.argmin(pbestval)
                    gbestval = pbestval[idx1]

                elif(minmax == 2):
                    idx1 = np.argmin(np.power((pbestval - np.ones_like(pbestval)) * errgoal, 2))
                    gbestval = pbestval[idx1]

                gbest = pbest[idx1, :]

            sentryval = gbestval
            sentry = gbest

        if(rstflg == 0):
            if(minmax == 0):
                pbestval = pbestval.reshape(-1, 1)
                tempi = np.where(pbestval >= out)
                pbestval[tempi] = out[tempi]
                pbest[tempi, :] = pos[tempi, :]

                idx1 = np.argmin(pbestval)
                iterbestval = pbestval[idx1]

                if(gbestval >= iterbestval):
                    gbestval = iterbestval
                    gbest = pbest[idx1, :]



        rannum1 = np.random.uniform(size = (ps, D))
        rannum2 = np.random.uniform(size = (ps, D))

        if(i == 0):
            if(i <= iwe):
                iwt[i] = (((iw2 - iw1)/(iwe - 1)) * (i-1) + iw1)
            
            else:
                iwt[i] = (iw2)
        
        else:
            if(i <= iwe):
                iwt.append(((iw2 - iw1)/(iwe - 1)) * (i-1) + iw1)
            
            else:
                iwt.append(iw2)

        ac11 = np.multiply(rannum1, ac1)
        ac22 = np.multiply(rannum2, ac2)

        vel = np.multiply(iwt[i], vel) + np.multiply(ac11, (pbest - pos)) + np.multiply(ac22, np.tile(gbest, (ps, 1)) - pos)

        vel = np.multiply((vel <= velmaskmin), velmaskmin) + np.multiply((vel > velmaskmin), vel)
        vel = np.multiply((vel >= velmaskmax), velmaskmax) + np.multiply((vel < velmaskmax), vel)

        pos = pos + vel

        minposmask_throwaway = pos <= posmaskmin
        minposmask_keep = pos > posmaskmin
        maxposmask_throwaway = pos >= posmaskmax
        maxposmask_keep = pos < posmaskmax

        pos = np.multiply(minposmask_throwaway, posmaskmax) + np.multiply(minposmask_keep, pos)
        pos = np.multiply(maxposmask_throwaway, posmaskmax) + np.multiply(maxposmask_keep, pos)

        vel = np.multiply(vel, minposmask_keep) + np.multiply(-vel, minposmask_throwaway)
        vel = np.multiply(vel, maxposmask_keep) + np.multiply(-vel, maxposmask_throwaway)

        tmp1 = abs(tr[0, i] - gbestval)
        if(tmp1 > ergrd):
            cnt2 = 0

        elif(tmp1 <= ergrd):
            cnt2 += 1
            if(cnt2 >= ergrdep):
                break





    out_temp = np.concatenate((gbest.T, gbestval))
    second_temp = [i for i in range(1, te + 1)]
    third_temp = tr[tr != np.array(None)]

    return out_temp, pre, second_temp, third_temp
    