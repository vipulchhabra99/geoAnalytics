import numpy as np

def forcerow(inp):
    temp = np.prod(list(inp.shape))
    return np.reshape(inp, (1, temp))

def forcecol(inp):
    temp = np.prod(list(inp.shape))
    return np.reshape(inp, (temp, 1))


def normat(x, newminmax, flag):

    if(flag == 0):
        a = x.min()
        b = x.max()

        if(abs(a) > abs(b)):
            large = a
            small = b

        else:
            large = b
            small = a

        if(np.size(newminmax, axis=0) != 1):
            raise Exception("Error: for method=0, range vector must be a 2 element row vector")

        den = abs(large - small)
        range_temp = newminmax[1] - newminmax[0]

        if(den == 0):
            out = x

        else:
            z21 = (x - a)/den
            out = z21* range_temp + newminmax[0] * np.ones_like(z21)
        
    elif(flag == 1):
        a = x.min(axis = 0)
        b = x.max(axis = 0)

        large = np.zeros_like(a)
        small = np.zeros_like(b)

        for i in range(len(b)):
            if(abs(a[i]) > abs(b[i])):
                large[i] = a[i]
                small[i] = b[i]

            else:
                large[i] = b[i]
                small[i] = a[i]

        den = abs(large - small)
        temp = list(newminmax.shape)

        if(temp[0] * temp[1] == 2):
            first_matrix = np.multiply(newminmax[0], np.ones_like(x[0, :]))
            second_matrix = np.multiply(newminmax[1], np.ones_like(x[0, :]))
            newminmaxA = np.concatenate((first_matrix, second_matrix))

        elif(temp[0] > 2):
            raise Exception('Error: for method=1, range matrix must have 2 rows and same columns as input matrix')

        else:
            newminmaxA = newminmax

        range_temp = np.array([newminmaxA[1, :] - newminmaxA[0, :]])

        out = np.zeros(shape=(len(x[:, 0]), len(b)))
        z21 = np.zeros(shape=(len(x[:, 0]), len(b)))
        for j in range(len(x[:, 0])):
            for i in range(len(b)):
                if(den[i] == 0):
                    out[j, i] = x[j, i]

                else:
                    z21[j, i] = (x[j, i] - a[i])/den[i]
                    out[j, i] = (z21[j, i] * range_temp[0, i])+ newminmaxA[0, i]

    elif(flag == 2):
        a = x.min(axis = 0)
        b = x.max(axis = 0)

        large = np.zeros(len(b))
        small = np.zeros(len(b))
        
        for i in range(len(b)):
            if(np.abs(a[i]) > np.abs(b[i])):
                large[i] = a[i]
                small[i] = b[i]

            else:
                large[i] = b[i]
                small[i] = a[i]

        den = np.abs(large - small)
        temp = np.array(list(newminmax.shape))

        if(temp[0] * temp[1] == 2):
            first_matrix = np.multiply(newminmax[0], np.ones_like(x[:, 0]))
            second_matrix = np.multiply(newminmax[1], np.ones_like(x[:, 0]))
            newminmaxA = np.column_stack((first_matrix, second_matrix))

        elif(temp[1] > 2):
            raise Exception('Error: for method=2, range matrix must have 2 columns and same rows as input matrix')

        else:
            newminmaxA = newminmax

        range_temp = newminmaxA[:, 1] - newminmaxA[:, 0]

        out = np.zeros(shape=(len(b), len(x[0, :])))
        z21 = np.zeros(shape=(len(b), len(x[0, :])))
        for j in range(len(x[0, :])):
            for i in range(len(b)):
                if(den[i] == 0):
                    out[i, j] = x[i, j]

                else:
                    z21[i, j] = np.divide((x[i, j] - a[i]), [forcecol(den[i])])
                    out[i, j] = np.matmul(z21[i, j], range_temp[i, 0]) + newminmaxA[i, 0]
                    


    return out

