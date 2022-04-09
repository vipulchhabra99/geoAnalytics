import math
import numpy as np
from time import process_time
from geotiff import GeoTiff
import geoAnalytics as ga
from numpy.core.fromnumeric import var
from .pso_Trelea_vectorized_update import *
import geoAnalytics.histif.src.global_vars as global_vars
from matplotlib import pyplot as plt
from .FFT import FFT
import tifffile
from sklearn.neighbors import KDTree
import rioxarray as rxr
from osgeo import gdal
from .fill_missing_pixels import fill_pixels


def check_missing_pixels(input_frame):
    """
        For checking if there exists any missing pixels
    """
    temp_frame = np.isnan(input_frame)
    missing_pixels = np.argwhere(temp_frame == True)

    if(len(missing_pixels) == 0):
        return False

    else:
        return True


def main_psf(coarse_img_t0=None, fine_img_t0=None, coarse_img_t1=None, params=None, iter=200, flag=0, neighbors=4, old_version=False):

    """
        The main function for performing fusion
    Returns:
        _numpy_array_: __The fused image or Predticed image__
    """
    
    if(flag == 0):

        img = GeoTiff(fine_img_t0)
        fine1 = np.array(img.read())
        pre_para = None

        img = GeoTiff(coarse_img_t0)
        coarse1 = np.array(img.read())

        img = GeoTiff(coarse_img_t1)
        coarse2 = np.array(img.read())

    elif(flag == 1):
        fine1 = fine_img_t0
        coarse1 = coarse_img_t0
        coarse2 = coarse_img_t1


    fn = np.size(fine1, 0)
    cn = np.size(coarse1, 0)

    global_vars.edge = (cn - fn)/2
    xx = global_vars.edge + 1
    yy = fn + global_vars.edge
    global_vars.N = yy - xx + 1

    limits = np.size(fine1, 2)
    pre_para = None
    channel_image = []

    for global_vars.iband in range(limits):
        global_vars.count_temp = 1
        global_vars.LR1 = fine1[:, :, global_vars.iband]

        if(check_missing_pixels(global_vars.LR1)):
            raise Exception("Missing pixels in the fine_t0 image!")
            # global_vars.LR1 = fill_pixels(global_vars.LR1, neighbors=neighbors)

        global_vars.HR1 = coarse1[:, :, global_vars.iband]

        if(check_missing_pixels(global_vars.HR1)):
            raise Exception("Missing pixels in the coarse_t0 image!")
            # global_vars.HR1 = fill_pixels(global_vars.HR1, neighbors=neighbors)

        global_vars.HR2 = coarse2[:, :, global_vars.iband]
        if(check_missing_pixels(global_vars.HR2)):
            raise Exception("Missing pixels in the coarse_t1 image!")
            # global_vars.HR2 = fill_pixels(global_vars.HR2, neighbors=neighbors)

        global_vars.LR1 = global_vars.LR1.reshape(
            1, int(global_vars.N*global_vars.N))

        functname = 'optima'
        dims = 5
        varrange = params
        mvden = 2
        mv = []

        for i in range(dims):
            mv.append((varrange[i][1] - varrange[i][0]) / mvden)

        minmax = 0
        plotfcn = 'goplotso'
        shw = 0
        ps = 30
        epoch = iter
        ac = [2.0, 2.0]
        Iwt = [0.9, 0.6]
        wt_end = 50
        errgrad = 1e-99
        errgraditer = 10
        errgoal = None
        modl = 0
        PSOseed = 0
        PSOseedValue = np.tile(np.array([0]), (ps, 1))
        psoparams = [shw, epoch, ps, ac[0], ac[1], Iwt[0], Iwt[1],
                     wt_end, errgrad, errgraditer, errgoal, modl, PSOseed]

        pso_out, HR1_psf, tr, te = pso_Trelea_vectorized_update(
            functname, dims, [mv, varrange, minmax, psoparams, plotfcn, PSOseedValue])

        if(pre_para is None):
            pre_para = pso_out.reshape(-1, 1)

        else:
            pre_para = np.column_stack((pre_para, pso_out))

        if(global_vars.iband > 3):
            global_vars.bpara = np.append(
                global_vars.bpara, np.zeros((dims, 1)), axis=1)

        global_vars.bpara[:, global_vars.iband] = np.rint(
            pre_para[:dims, global_vars.iband])

        HR2_psf = FFT(global_vars.bpara[:, global_vars.iband], global_vars.HR2)
        HR2_p = np.multiply(np.divide(HR2_psf, HR1_psf), global_vars.LR1)

        HR1_psf_cal = FFT(
            global_vars.bpara[:, global_vars.iband], global_vars.HR1)
        predicted_HR1_p = np.multiply(
            np.divide(HR1_psf_cal, HR1_psf), global_vars.LR1)

        if(old_version is False):
            error = global_vars.LR1 - predicted_HR1_p

        else:
            error = 0

        if(global_vars.pre_image is None):
            global_vars.pre_image = (
                HR2_p + error).reshape(int(global_vars.N), int(global_vars.N), 1)
        else:
            global_vars.pre_image = np.dstack(
                (global_vars.pre_image, (HR2_p + error).reshape(int(global_vars.N), int(global_vars.N), 1)))

        channel_image.append(HR2_p.reshape(
            int(global_vars.N), int(global_vars.N)))

    if(flag == False):
        pre_lidar_dem = rxr.open_rasterio(fine_img_t0, masked=True)
        sr = list(pre_lidar_dem.rio.resolution())[0]
    else:
        sr = 2
    global_vars.bpara[0:4, :] = np.multiply(global_vars.bpara[0:4, :], sr)
    image_shape = list(global_vars.pre_image.shape)
    return global_vars.pre_image, np.array(channel_image)

# if __name__ == '__main__':
#     params = np.array([[0, 3], [0, 3], [-1, 1], [-1, 1], [35, 65]])
#     img_data_new, final_img = main_psf("coarse_t0.tif", "fine_t0.tif", "coarse_t1.tif", params, 1)
#     print(img_data_new)
#     print(img_data_new.shape)
#     plt.imshow(img_data_new, interpolation='nearest')
#     plt.axis('off')
#     cur_shape = list(img_data_new.shape)
#     print(final_img.shape)

#     dst_filename = 'test.tif'
#     x_pixels = (final_img[0]).shape[0]  # number of pixels in x
#     y_pixels = (final_img[0]).shape[1]  # number of pixels in y
#     driver = gdal.GetDriverByName('GTiff')
#     dataset = driver.Create(dst_filename,x_pixels, y_pixels, 4,gdal.GDT_Float32)
#     dataset.GetRasterBand(1).WriteArray(final_img[0])
#     dataset.GetRasterBand(2).WriteArray(final_img[1])
#     dataset.GetRasterBand(3).WriteArray(final_img[2])
#     dataset.GetRasterBand(4).WriteArray(final_img[3])
#     data0 = gdal.Open("coarse_t1.tif")
#     geotrans=data0.GetGeoTransform()
#     proj=data0.GetProjection()
#     dataset.SetGeoTransform(geotrans)
#     dataset.SetProjection(proj)
#     dataset.FlushCache()
#     dataset=None


#     # tifffile.imsave('test.tiff', img_data_new)
#     plt.show()
