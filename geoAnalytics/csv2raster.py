from osgeo import gdal
import pandas as pd
import os

class csv2raster:
    def __init__(self,input_file='', output_file='output.nc', sep=" ", dataframe=''):
        self.input_file = input_file
        self.inputfile_sep = sep
        self.output_file = output_file
        self.dataFrame = dataframe

    def toraster(self):
        if self.input_file != '':
            self.dataFrame = pd.read_csv(self.input_file, 
                                         sep=self.inputfile_sep, 
                                         header=None, index_col=None)
        self.dataFrame.to_csv("xyzformat.xyz", index=False, header=None, sep=" ")
        raster = gdal.Translate(self.output_file, "xyzformat.xyz")
        os.remove("xyzformat.xyz")


if __name__ == "__main__":
    csv2raster = Csv2raster("MI_MAP_03_N00E001S01E002SC.csv",
                            "MI_MAP_03_N00E001S01E002SC.nc", sep=" ")
    csv2raster.toraster()