from geoAnalytics.config import config
from osgeo import gdal
import pandas as pd
import math
import numpy as np
from .histif.src.main_psf import main_psf
from .histif.src.evaluation import display_result, find_cc, find_rmse, find_mean_absolute_difference
import geoAnalytics.database as db
import uuid

def create_image_array(repository_name, envelope_mode = False, envelope_params = None):
    """
    Creates a image array from a repository

    Args:
        repository_name (_string_): _Name of postgres repository_

    Returns:
        numpy_array :  Array containing the pixel values of the image
        tuple : The geocoordinates of the image.
    """

    df = db.getDataframe(repositoryName = repository_name)
    
    x_points = df.x.unique()
    y_points = df.y.unique()

    num_bands = len(df.columns) - 2

    x_image_map = {}
    y_image_map = {}

    for i in range(len(x_points)):
        x_image_map[x_points[i]] = i

    for i in range(len(y_points)):
        y_image_map[y_points[i]] = i


    image_frame = np.zeros((len(x_points), len(y_points),num_bands))

    image_vec = df.to_numpy(dtype = 'float64')
    # print(image_vec.shape)
    # print(image_frame.shape)

    for i in range(len(image_vec)):
        for band_num in range(num_bands):
            image_frame[y_image_map[image_vec[i][1]], x_image_map[image_vec[i][0]],band_num] = image_vec[i][band_num+2]

    gap_x = x_points[1] - x_points[0]
    gap_y = y_points[1] - y_points[0]

    starting_x = x_points[0] - (gap_x/2)
    starting_y = y_points[0] - (gap_y/2)
    geo_coordinates = (starting_x, gap_x, 0.0, starting_y, 0.0, gap_y)

    print(image_frame.shape)
    return image_frame, geo_coordinates

def get_recommended_params(scaleFactor):
    """
    Returns the recommended parameters for HISTIF

    Args:
        scaleFactor (_float_): _The scale factor of the image_

    Returns:
        numpy_array : The recommended parameters for HISTIF
    """
    fmwh_x1 = math.floor(scaleFactor / 2)
    fmwh_x2 = round(scaleFactor * 2.5)
    fmwh_y1 = math.floor(scaleFactor / 2)
    fmwh_y2 = round(scaleFactor * 2.5)
    shiftx_start = -scaleFactor
    shiftx_end = scaleFactor
    shifty_start = -scaleFactor
    shifty_end = scaleFactor
    rot_angle_f = 35
    rot_angle_e = 65

    params = np.array([[fmwh_x1, fmwh_x2], [fmwh_y1, fmwh_y2], [shiftx_start, shiftx_end], [shifty_start, shifty_end], [rot_angle_f, rot_angle_e]])
    return params


def store_image(image_frame, DestinationFileName, geotrans = None):
    
    """
    Stores an image in a raster file

    Args:
        image_frame (_numpy_array_): _The image to be stored_
        DestinationFileName (_string_): _The name of the raster file_
        geotrans (_tuple_): _The geotransform info of the image_
    """
    
    x_pixels = (image_frame[0]).shape[0]  # number of pixels in x
    y_pixels = (image_frame[0]).shape[1]  # number of pixels in y
    print(x_pixels, y_pixels)
    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(DestinationFileName,x_pixels, y_pixels, len(image_frame),gdal.GDT_Float32)
    
    for band_range in range(len(image_frame)):
         dataset.GetRasterBand(band_range+1).WriteArray(image_frame[band_range])
    
    dataset.FlushCache()
    
    if(geotrans is not None):
        dataset.SetGeoTransform(geotrans)

    dataset = None

def HISTIF_improved(scaleFactor, FineImageRepositoryAtT0, CoarseImageRepositoryAtT0, CoarseImageRepositoryAtT1, iterations = 100, recommended_params = True, fmwh_x1 = None, fmwh_x2 = None, fmwh_y1 = None, fmwh_y2 = None, shiftx_start = None, shiftx_end = None, shifty_start = None, shifty_end = None, rot_angle_f = None, rot_angle_e = None, neighbors = 4, DestinationFileName = f"{str(uuid.uuid4())}.tif", EnvelopeMode = False, EnvelopeParams = None):
    """
    Performs HISTIF improved version
    Args:
        scaleFactor (_float_): _The_ scale factor of the image_
        FineImageRepositoryAtT0 (_string_): _Name of the fine image repository_
        CoarseImageRepositoryAtT0 (_string_): _Name of the coarse image repository_
        CoarseImageRepositoryAtT1 (_string_): _Name of the coarse image repository_
        iterations (int, optional): _The number of iterations _. Defaults to 100.
        recommended_params (bool, optional): _Flag to identify the use of recommended parameters_. Defaults to True.
        neighbors (int, optional): _The number of neighbours to consider for imputing missing values_. Defaults to 4.
        DestinationFileName (str, optional): _The name of the output file_. Defaults to "result.tif".
    """
    if(recommended_params is False):
        params = np.array([[fmwh_x1, fmwh_x2], [fmwh_y1, fmwh_y2], [shiftx_start, shiftx_end], [shifty_start, shifty_end], [rot_angle_f, rot_angle_e]])
    
    else:
        params = get_recommended_params(scaleFactor)

    fine_t0, geo_fin_t0 = create_image_array(FineImageRepositoryAtT0, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    coarse_t0, geo_cor_t0 = create_image_array(CoarseImageRepositoryAtT0, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    coarse_t1, geo_cor_t1 = create_image_array(CoarseImageRepositoryAtT1, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    
    img_data_new, final_img = main_psf(coarse_t0, fine_t0, coarse_t1, params, iterations, flag = 1, neighbors = neighbors)

    store_image(final_img, DestinationFileName, geo_fin_t0)

def HISTIF(scaleFactor, FineImageRepositoryAtT0, CoarseImageRepositoryAtT0, CoarseImageRepositoryAtT1, iterations = 100, recommended_params = True, fmwh_x1 = None, fmwh_x2 = None, fmwh_y1 = None, fmwh_y2 = None, shiftx_start = None, shiftx_end = None, shifty_start = None, shifty_end = None, rot_angle_f = None, rot_angle_e = None, neighbors = 4, DestinationFileName = f"{str(uuid.uuid4())}.tif", EnvelopeMode = False, EnvelopeParams = None):
    
    """
    Performs traditional version of HISTIF
    Args:
        scaleFactor (_float_): _The_ scale factor of the image_
        FineImageRepositoryAtT0 (_string_): _Name of the fine image repository_
        CoarseImageRepositoryAtT0 (_string_): _Name of the coarse image repository_
        CoarseImageRepositoryAtT1 (_string_): _Name of the coarse image repository_
        iterations (int, optional): _The number of iterations _. Defaults to 100.
        recommended_params (bool, optional): _Flag to identify the use of recommended parameters_. Defaults to True.
        neighbors (int, optional): _The number of neighbours to consider for imputing missing values_. Defaults to 4.
        DestinationFileName (str, optional): _The name of the output file_. Defaults to "result.tif".
    """

    if(recommended_params is False):
        params = np.array([[fmwh_x1, fmwh_x2], [fmwh_y1, fmwh_y2], [shiftx_start, shiftx_end], [shifty_start, shifty_end], [rot_angle_f, rot_angle_e]])
    
    else:
        params = get_recommended_params(scaleFactor)

    fine_t0, geo_fin_t0 = create_image_array(FineImageRepositoryAtT0, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    coarse_t0, geo_cor_t0 = create_image_array(CoarseImageRepositoryAtT0, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    coarse_t1, geo_cor_t1 = create_image_array(CoarseImageRepositoryAtT1, envelope_mode = EnvelopeMode, envelope_params = EnvelopeParams)
    
    img_data_new, final_img = main_psf(coarse_t0, fine_t0, coarse_t1, params, iterations, flag = 1, neighbors = neighbors, old_version = True)

    store_image(final_img, DestinationFileName, geo_fin_t0)


def evaluate_results(actual_result, predicted_result):
    """_summary_
    Compares the results of two images
    Args:
        first_result (_numpy_array_): _The first image_
        second_result (_numpy_array_): _The second image_
    """

    first_res, _ = create_image_array(actual_result)
    second_res, _ = create_image_array(predicted_result)
    print()
    display_result("Correlation Coefficient", find_cc(first_res, second_res, file_read = False))
    print()
    display_result("Root Mean Square Error (RMSE)", find_rmse(first_res, second_res, file_read = False))
    print()
    display_result("Mean Absolute Error", find_mean_absolute_difference(first_res, second_res, file_read = False))