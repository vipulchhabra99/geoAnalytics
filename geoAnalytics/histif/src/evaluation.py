import numpy as np
from geotiff import GeoTiff
import pandas as pd
from sklearn.metrics import mean_squared_error
import math

class DataReader:

    def __init__(self, observed, predicted) -> None:
        self.observed = GeoTiff(observed)
        self.predicted = GeoTiff(predicted)

    def read_images(self):
        obs = np.array(self.observed.read())
        pred = np.array(self.predicted.read())
        return obs, pred

def find_cc(observed, predicted, file_read = True):
    """Finding Correlation Coefficient"""

    if(file_read):
        input_data = DataReader(observed, predicted)
        obs, pred = input_data.read_images()
    
    else:
        obs, pred = observed, predicted

    band_wise_data = []

    for band in range(obs.shape[2]):
        x_band = pd.Series(obs[:, :, band].flatten())
        y_band = pd.Series(pred[:, :, band].flatten())
        band_wise_data.append(x_band.corr(y_band))
        
    return band_wise_data

def find_rmse(observed, predicted, file_read = True):
    """Finding Root Mean Square Error"""

    if(file_read):
        input_data = DataReader(observed, predicted)
        obs, pred = input_data.read_images()
    
    else:
        obs, pred = observed, predicted

    band_wise_error = []

    for band in range(obs.shape[2]):
        band_wise_error.append(math.sqrt(mean_squared_error(obs[:, :, band], pred[:, :, band])))
        
    return band_wise_error

def find_mean_absolute_difference(observed, predicted, file_read = True):
    """Finding Mean Absolute Difference"""

    if(file_read):
        input_data = DataReader(observed, predicted)
        obs, pred = input_data.read_images()
    
    else:
        obs, pred = observed, predicted

    band_wise_error = []

    for band in range(obs.shape[2]):
        band_wise_error.append(np.mean(abs(obs[:, :, band] - pred[:, :, band])))
        
    return band_wise_error

def display_result(param_name, values):

    for i in range(len(values)):
        print("The {} for the {} is {}".format(param_name, f"B{i}", values[i]))

# display_result("Correlation Coefficient", find_cc("fine_t0.tif", "eval_test-without-error.tif"))
# display_result("Root Mean Square Error (RMSE)", find_rmse("fine_t0.tif", "eval_test-without-error.tif"))
# display_result("Mean Absolute Error", find_mean_absolute_difference("fine_t0.tif", "eval_test-without-error.tif"))