import numpy as np
from osgeo import gdal
import pandas as pd
import random
import sys
import os
import subprocess


class Csv2raster:
    """"
    Usage --> python3 csv2raster.py  inputfile_path
    """

    def __init__(self, input_file, sep=" "):

        if isinstance(input_file, str):
            self.dataFrame = pd.read_csv(
                input_file, sep=" ", header=None, index_col=None)
        elif isinstance(input_file, pd.DataFrame):
            self.dataFrame = input_file

        self.band_count = self.dataFrame.shape[1] - 2
        self.columns = ['x', 'y']
        for i in range(self.band_count):
            self.columns.append("b" + str(i + 1))
        self.dataFrame.columns = self.columns
        self.dataFrame.to_csv("uneven.csv", index=False)

    def save_raster_image(self, outFile):
        for i in range(self.band_count):
            self.output_file = "raster_" + self.columns[i + 2] + "_" + str(random.randint(0, 100000)) + ".nc"
            f = open("uneven.vrt", "w")
            f.write("<OGRVRTDataSource>\n \
                <OGRVRTLayer name=\"uneven\">\n \
                    <SrcDataSource>uneven.csv</SrcDataSource>\n \
                    <GeometryType>wkbPoint</GeometryType>\n \
                    <GeometryField encoding=\"PointFromColumns\" x=\"x\" y=\"y\" z=\"self.columns[i+2]\"/>\n \
                </OGRVRTLayer>\n \
                    </OGRVRTDataSource>")
            f.close()
            r = gdal.Rasterize(self.output_file, "uneven.vrt",
                               xRes=1, yRes=-1, attribute=self.columns[i + 2])
            r = None

            g = gdal.Grid("unevenInt.tif", "uneven.vrt")
            g = None

            os.remove("uneven.vrt")
        os.remove("uneven.csv")
        os.remove("unevenInt.tif")
        if outFile[-3:] == '.nc':
            buffer = 'cdo cat raster_b*.nc ' + outFile
            print(subprocess.getstatusoutput(buffer))
            buffer = 'rm raster_*'
            print(subprocess.getstatusoutput(buffer))
        elif outFile[-3:] == 'iff' or outFile[-3:] == 'tif':
            buffer = 'cdo cat raster_b*.nc combined.nc'
            print(subprocess.getstatusoutput(buffer))
            buffer = 'gdal_translate -of GTiff combined.nc ' + outFile
            print(subprocess.getstatusoutput(buffer))
            buffer = 'rm raster_*'
            print(subprocess.getstatusoutput(buffer))
            buffer = 'rm combined.nc'
            print(subprocess.getstatusoutput(buffer))


if __name__ == "__main__":
    csv2raster = Csv2raster(input_file=sys.argv[1])
    csv2raster.save_raster_image()
