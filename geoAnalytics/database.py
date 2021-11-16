from geoAnalytics.config import config
from geoAnalytics import csv2raster as c2r
from shapely import geos, wkb, wkt
import psycopg2
import pandas as pd
import os
import subprocess
import glob
from geoAnalytics import raster2tsv
import sys
import numpy as Numeric
from osgeo import gdal


class database:
    conn = ""
    cur = ""

    def connect(dbName, hostIP, user, password, port=5432):
        """
        Connect to the database

        :param dbName: name of the database
        :param hostIP: host IP
        :param user: user name
        :param password: password
        :param port: port
        """
        database.conn = None
        if dbName != "":
            with open('database.ini', "w") as dbFile:
                buffer = "[postgresql]\nhost = " + hostIP + "\nport = " + str(
                    port) + "\ndatabase = " + dbName + "\nuser = " + user + "\npassword = " + password
                dbFile.write(buffer)
                dbFile.close()
        database.testDatabaseConnection()

    def disconnect(self):
        """
        Disconnect from the database
        """
        if database.conn is not None:
            print("Disconnecting from database")
            database.conn.close()
            print("Disconnected from database")

    def testConnection(self):
        """
        Test the connection to the database
        """

        database.conn = None
        try:
            # read database configuration
            params = config()
            # connect to the PostgreSQL database
            database.conn = psycopg2.connect(**params)
            # create a new cursor
            database.curr = database.conn.cursor()
            database.curr.execute("select version()")
            for item in database.curr:
                print(item)
            print('You are now connected')
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    def reConnect(dbName, hostIP, user, password, port=5432):
        """
        Edit the connection to the database

        :param dbName: name of the database
        :param hostIP: host IP
        :param user: user name
        :param password: password
        :param port: port
        """
        database.conn = None
        if dbName != "":
            with open('database.ini', "w") as dbFile:
                buffer = "[postgresql]\nhost = " + hostIP + "\nport = " + str(
                    port) + "\ndatabase = " + dbName + "\nuser = " + user + "\npassword = " + password
                dbFile.write(buffer)
                dbFile.close()
        database.testDatabaseConnection()

    def createRepository(RepositoryName, totalBands, SRID=4326, coordsFrontOrBack='front'):
        """
        Create a Repository in the database

        :param RepositoryName: name of the Repository
        :param totalBands: total number of bands
        :param SRID: spatial reference ID
        :param coordsFrontOrBack: front or back
        """
        # total bands is number
        query = ""
        if coordsFrontOrBack == 'front':
            query += "geog geometry(POINT," + str(SRID) + "),"
        for i in range(1, totalBands + 1):
            query += 'b' + str(i) + ' float,'
        if coordsFrontOrBack == 'back':
            query += "geog geometry(POINT," + str(SRID) + ")"
        createRepository = "create table " + RepositoryName + "(" + query + ");"
        if createRepository[-3:] == ",);":
            createRepository = createRepository[:-3] + ");"
        database.curr.execute(createRepository)
        database.conn.commit()
        print('Repository created')

def insertRaster(Repository, filename, totalBands, SRID=4326):
    """
    Insert a TIFF file into the database

    :param Repository: name of the Repository
    :param filename: name of the TIFF file
    :param totalBands: number of bands
    :param SRID: spatial reference ID
    """
    query = "python3 gdal2xyz.py"
    database.__r2tsv(totalBands, filename)
    with open("temp1.txt") as inFile:
        with open("temp2.txt", "w") as outFile:
            for lines in inFile:
                word = lines.strip()
                word = word.split(" ")

                Latitude = word[0]
                # word.pop(0)
                Longitude = word[1]
                # word.pop(0)
                buffer = "POINT(" + Latitude + " " + Longitude + ")"
                p = wkt.loads(buffer)
                new = wkb.dumps(p, hex=True, srid=SRID)

                sqlLine = new
                for w in word[2:]:
                    sqlLine += ' ' + w
                sqlLine += "\n"
                outFile.write(sqlLine)
            outFile.close()
        inFile.close()

    database.insertCSVFile("temp2.txt", ' ', Repository)
    if os.path.exists("temp1.txt"):
        os.remove("temp1.txt")
    if os.path.exists("temp2.txt"):
        os.remove("temp2.txt")

    def insertCSV(filename, seperator, RepositoryName):
        """
        Insert a CSV file into the database

        :param filename: name of the CSV file
        :param seperator: seperator
        :param RepositoryName: name of the Repository
        """

        with open(filename) as inFile:
            with open("temp_" + filename, "w") as tempFile:
                for lines in inFile:
                    word = lines.strip()
                    word = word.split(seperator)
                    sqlLine = ""
                    for w in word:
                        sqlLine += w + " "
                    sqlLine = sqlLine[:-1] + "\n"
                    tempFile.write(sqlLine)
                tempFile.close()
            inFile.close()

        copy_file = "copy " + RepositoryName + " from '" + str(
            os.getcwd()) + "/temp_" + filename + "' delimiters '" + ' ' + "' csv;"
        database.curr.execute(copy_file)

        # finished
        database.conn.commit()
        print('file has been inserted')

        if os.path.exists("temp_" + filename):
            os.remove("temp_" + filename)

    def __r2tsv(self,  endBand, srcfile):
        """
        Convert a raster to a tsv file

        :param startBand: start band
        :param endBand: end band
        :param srcfile: source file
        :param dstfile: destination file
        """
        dstfile = 'temp.txt'
        band_nums = range(1, endBand + 1)
        srcwin = None
        if band_nums == []: band_nums = [1]

        # Open source file. 
        srcds = gdal.Open(srcfile)
        if srcds is None:
            print('Could not open %s.' % srcfile)
            sys.exit(1)

        bands = []
        for band_num in band_nums:
            band = srcds.GetRasterBand(band_num)
            if band is None:
                print('Could not get band %d' % band_num)
                sys.exit(1)
            bands.append(band)
        gt = srcds.GetGeoTransform()

        # Collect information on all the source files.
        if srcwin is None:
            srcwin = (0, 0, srcds.RasterXSize, srcds.RasterYSize)

        # Open the output file.
        if dstfile is not None:
            dst_fh = open(dstfile, 'wt')
        else:
            dst_fh = sys.stdout
        band_format = ("%g " * len(bands)).rstrip() + '\n'

        # Setup an appropriate print format.
        if abs(gt[0]) < 180 and abs(gt[3]) < 180 \
                and abs(srcds.RasterXSize * gt[1]) < 180 \
                and abs(srcds.RasterYSize * gt[5]) < 180:
            format = '%.10g %.10g %s'
        else:
            format = '%.3f %.3f %s'

        # Loop emitting data.
        for y in range(srcwin[1], srcwin[1] + srcwin[3]):
            data = []
            for band in bands:
                band_data = band.ReadAsArray(srcwin[0], y, srcwin[2], 1)
                band_data = Numeric.reshape(band_data, (srcwin[2],))
                data.append(band_data)

            for x_i in range(0, srcwin[2]):
                x = x_i + srcwin[0]
                geo_x = gt[0] + (x + 0.5) * gt[1] + (y + 0.5) * gt[2]
                geo_y = gt[3] + (x + 0.5) * gt[4] + (y + 0.5) * gt[5]
                x_i_data = []
                for i in range(len(bands)):
                    x_i_data.append(data[i][x_i])
                band_str = band_format % tuple(x_i_data)
                line = format % (float(geo_x), float(geo_y), band_str)
                dst_fh.write(line)



    def insertLBL(Repository, inputFolder, startBand, endBand):
        """
        Insert a LBL file into the database

        :param Repository: name of the Repository
        :param inputFolder: folder containing the LBL files
        :param startBand: start band
        :param endBand: end band
        """
        fileExtension = "lbl"
        outputFolder = ''
        path = inputFolder + '/*.' + fileExtension
        # reading each file in a folder
        my_df = pd.DataFrame()
        file = glob.glob(path)
        listOfDataframes = []
        mainDataFrame = pd.DataFrame()
        out_csv = ('rawData.tsv')
        text = ''
        header = ['0']
        for bandNo in range(startBand, endBand + 1):
            text = text + '-band ' + str(bandNo) + ' '
            header.append('-band' + str(bandNo))

        if os.path.exists(out_csv):
            os.remove(out_csv)

        for file in glob.glob(path):
            # extracting output filename
            parameters = text + file + ' ' + out_csv
            raster2tsv.raster2tsv(parameters)
            mainDataFrame = pd.read_csv(out_csv, header=None, sep='\t')
            mainDataFrame.columns = header
        # mainDataFrame = mainDataFrame.set_index('coordinate')
        mainDataFrame.to_csv('rawData.tsv', index=False, header=False, sep='\t')

        with open("rawData.tsv") as inFile:
            with open("rawData2.tsv", "w") as outFile:
                for lines in inFile:
                    word = lines.strip()
                    word = word.split("\t")

                    buffer = word[0]
                    p = wkt.loads(buffer)
                    new = wkb.dumps(p, hex=True, srid=4326)

                    sqlLine = new
                    for w in word[1:]:
                        sqlLine += ' ' + w
                    sqlLine += "\n"
                    outFile.write(sqlLine)
                outFile.close()
            inFile.close()

        database.insertCSVFile("rawData2.tsv", ' ', Repository)
        if os.path.exists("rawData.tsv"):
            os.remove("rawData.tsv")
        if os.path.exists("rawData2.tsv"):
            os.remove("rawData2.tsv")

    def deleteRepository(RepositoryName):
        """
        Delete a Repository from the database

        :param RepositoryName: name of the Repository
        """
        delete_Repository = "drop table " + RepositoryName + ";"
        database.curr.execute(delete_Repository)
        database.conn.commit()
        print('Repository deleted')

    def cloneRepository(RepositoryName, cloneRepositoryName):
        """
        Clone a Repository from the database

        :param RepositoryName: name of the Repository
        :param cloneRepositoryName: name of the cloned Repository
        """
        clone_Repository = "create table " + cloneRepositoryName + " as (select * from " + RepositoryName + ");"
        database.curr.execute(clone_Repository)
        database.conn.commit()
        print('Repository cloned')

    def changeRepositoryName(RepositoryName, newRepositoryName):
        """
        Change the name of a Repository in the database
        
        :param RepositoryName: name of the Repository
        :param newRepositoryName: new name of the Repository
        """
        changeRepositoryName = "ALTER TABLE IF EXISTS " + RepositoryName + " RENAME TO " + newRepositoryName + ";"
        database.curr.execute(changeRepositoryName)
        database.conn.commit()
        print('Repository name changed')

    def deleteBandInRepository(repositoryName, bandNumber):

        # This function will delete the band number attribute from the table.

    def getRaster(RepositoryName, rasterFileName, Xmin, Ymin, Xmax=0, Ymax=0, Bands="*"):
        """
        Get a raster image from the database

        :param RepositoryName: name of the Repository
        :param rasterFileName: name of the raster file
        :param Xmin: minimum X coordinate
        :param Ymin: minimum Y coordinate
        :param Xmax: maximum X coordinate
        :param Ymax: maximum Y coordinate
        :param Bands: bands to be extracted
        """
        # connect to database
        # create geoTIFF file
        # gDal transform to geoTIFF
        df = database.getDataframeForEnvelope(RepositoryName, Xmin, Ymin, Xmax, Ymax, Bands)
        database.dataFrame2Raster(df, rasterFileName)

    def dataFrame2Raster(dataframe, rasterFileName):
        """
        Create a raster image from a dataframe

        :param dataframe: dataframe
        :param rasterFileName: name of the raster file with no file extension.

        """

        # check rasterFile type
        gobi = rasterFileName[-3:]
        extension = '.tif'

        df = dataframe
        df = df.sort_values(['y', 'x'], ascending=[True, True])
        df = df.reset_index()
        df = df.drop(columns=["index"])
        dblen = len(df.columns) - 1
        for i in range(1, len(df.columns) - 1, 1):
            obj4 = c2r.csv2raster(output_file='output' + str(i) + '.nc', dataframe=df)
            obj4.toraster()
            columnDrop = 'b' + str(i)
            df = df.drop(columns=columnDrop)
        for i in range(1, dblen):
            colN = 'Band1,b' + str(i)
            file = 'output' + str(i) + '.nc'
            subprocess.check_call(['ncrename', '-v', colN, file])

        if rasterFileName[-3:] == '.nc':
            buffer = 'cdo cat output*.nc ' + rasterFileName
            print(subprocess.getstatusoutput(buffer))
        elif rasterFileName[-3:] == 'iff' or rasterFileName[-3:] == 'tif':
            buffer = 'cdo cat output*.nc combined.nc'
            print(subprocess.getstatusoutput(buffer))
            buffer = 'gdal_translate -of GTiff combined.nc ' + rasterFileName
            print(rasterFileName)
            print(subprocess.getstatusoutput(buffer))
            buffer = 'rm combined.nc'
            print(subprocess.getstatusoutput(buffer))

        print('raster generated')
        buffer = 'rm output*.nc'
        print(subprocess.getstatusoutput(buffer))

    def getDataframeForEnvelope(RepositoryName, Xmin, Ymin, Xmax, Ymax, Bands="*", SRID=4326):
        """
        Get a dataframe from the database for a given envelope

        :param RepositoryName: name of the Repository
        :param Xmin: minimum X coordinate
        :param Ymin: minimum Y coordinate
        :param Xmax: maximum X coordinate
        :param Ymax: maximum Y coordinate
        :param Bands: bands to be extracted
        :param SRID: spatial reference ID
        """

        # connect to database
        # create geoTIFF file
        # gDal transform to geoTIFF

        query = "SELECT ST_X(geog) as x, ST_Y(geog) as y, " + Bands + " FROM " + RepositoryName + " WHERE " + RepositoryName + ".geog && ST_MakeEnvelope(" + str(
            Xmin) + ',' + str(Ymin) + ',' + str(Xmax) + ',' + str(Ymax) + ");"
        dataFrameEnvelope = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameEnvelope = dataFrameEnvelope.drop(columns=["geog"])
        print('dataframe created')
        return dataFrameEnvelope

    def KNN(RepositoryName, X, Y, k=1000, Bands="*", SRID=4326):
        """
        Get a dataframe from the database for a point and its neighbors

        :param RepositoryName: name of the Repository
        :param X: X coordinate
        :param Y: Y coordinate
        :param k: number of neighbours
        :param Bands: bands to be extracted
        :param SRID: spatial reference ID
        """
        query = "SELECT ST_X(geom::geometry) as x, ST_Y(geom::geometry) as y, " + str(Bands) + " FROM " + str(
            RepositoryName) + " ORDER BY " + str(RepositoryName) + ".geom <-> 'SRID=" + str(SRID) + ";POINT(" + str(
            X) + ' ' + str(Y) + ")'::geometry limit " + str(k) + ";"
        dataFrameKNN = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameKNN = dataFrameKNN.drop(columns=["geom"])
        print('dataframe created')
        return dataFrameKNN

    def getRasterImageKNN(RepositoryName, rasterFileName="rasterFile.nc", X=0, Y=0, k=1000, Bands="*"):
        """
        Get a raster image from the database for a point and its neighbors

        :param RepositoryName: name of the Repository
        :param rasterFileName: name of the raster file
        :param X: X coordinate
        :param Y: Y coordinate
        :param k: number of neighbours
        :param Bands: bands to be extracted
        """
        # connect to database
        # create geoTIFF file
        # gDal transform to geoTIFF
        df = database.KNN(RepositoryName, X, Y, k, Bands)
        database.dataFrame2Raster(df, rasterFileName)
