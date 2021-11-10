from geoAnalytics.config import config
from shapely import geos, wkb, wkt
import psycopg2
import pandas as pd
from geoAnalytics import csv2raster as c2r
import os
import subprocess
import glob
from geoAnalytics import raster2tsv

class database:
    conn = ""
    cur = ""
    def connect(dbName="", hostIP="", user="", password="", port=5432):
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
            with open('database.ini',"w") as dbFile:
                buffer = "[postgresql]\nhost = " + hostIP +"\nport = " + str(port) +"\ndatabase = " + dbName +"\nuser = " + user + "\npassword = " + password
                dbFile.write(buffer)
                dbFile.close()                     
        database.testDatabaseConnection()
    
    def disconnect():
        """
        Disconnect from the database
        """
        if database.conn is not None:
            print("Disconnecting from database")
            database.conn.close()
            print("Disconnected from database")
                             
    def testDatabaseConnection():
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
                         
    def createTable(tableName, totalBands, SRID=4326, coordsFrontOrBack='front'):
        """
        Create a table in the database

        :param tableName: name of the table
        :param totalBands: total number of bands
        :param SRID: spatial reference ID
        :param coordsFrontOrBack: front or back
        """
        # total bands is number
        query = ""
        if coordsFrontOrBack=='front':
            query += "geog geometry(POINT," + str(SRID) + "),"
        for i in range(1,totalBands+1):
            query += 'b' + str(i) + ' float,'
        if coordsFrontOrBack=='back':
            query += "geog geometry(POINT," + str(SRID) + ")"
        create_table = "create table " + tableName + "(" + query + ");"
        if create_table[-3:] == ",);":
            create_table = create_table[:-3] + ");"
        database.curr.execute(create_table)
        database.conn.commit()
        print('table created')
    
    def insertCSVFile(filename,seperator, tableName):
        """
        Insert a CSV file into the database

        :param filename: name of the CSV file
        :param seperator: seperator
        :param tableName: name of the table
        """

        with open(filename) as inFile:
            with open("temp_" + filename,"w") as tempFile:
                for lines in inFile:
                    word = lines.strip()
                    word = word.split(seperator)
                    sqlLine = ""
                    for w in word:
                        sqlLine +=  w + " "
                    sqlLine = sqlLine[:-1] + "\n"
                    tempFile.write(sqlLine)
                tempFile.close()
            inFile.close()
                         
        copy_file = "copy " + tableName + " from '" + str(os.getcwd()) +  "/temp_" + filename + "' delimiters '" + ' ' + "' csv;"
        database.curr.execute(copy_file)

        # finished
        database.conn.commit()
        print('file has been inserted')
        
        if os.path.exists("temp_" + filename):
            os.remove("temp_" + filename)
        
            
    def insertTIFF(table="",filename="", bands=1, SRID=4326):
        """
        Insert a TIFF file into the database

        :param table: name of the table
        :param filename: name of the TIFF file
        :param bands: number of bands
        :param SRID: spatial reference ID
        """
        query = "python3 gdal2xyz.py"
        for i in range(1,bands+1):
            query += " -band " + str(i)
        query += " " + str(filename) + ' ' + os.getcwd() + "/temp1.txt"
        subprocess.getstatusoutput(query)
        with open("temp1.txt") as inFile:
            with open("temp2.txt", "w") as outFile:
                for lines in inFile:
                    word = lines.strip()
                    word = word.split(" ")

                    Latitude = word[0]
                    #word.pop(0)
                    Longitude = word[1]
                    #word.pop(0)
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
        
        database.insertCSVFile("temp2.txt",' ', table)
        if os.path.exists("temp1.txt"):
            os.remove("temp1.txt")
        if os.path.exists("temp2.txt"):
            os.remove("temp2.txt")
            
    def insertLBL(table,inputFolder,startBand, endBand):
        """
        Insert a LBL file into the database

        :param table: name of the table
        :param inputFolder: folder containing the LBL files
        :param startBand: start band
        :param endBand: end band
        """
        fileExtension = "lbl"
        outputFolder = ''
        path = inputFolder + '/*.'+fileExtension
        # reading each file in a folder
        my_df = pd.DataFrame()
        file = glob.glob(path)
        listOfDataframes = []
        mainDataFrame = pd.DataFrame
        out_csv = ('rawData.tsv')
        text = ''
        header = ['0']
        for bandNo in range(startBand, endBand + 1):
            text = text + '-band ' + str(bandNo) + ' '
            header.append('-band' + str(bandNo))

        if os.path.exists(out_csv):
            os.remove(out_csv)

        for file in glob.glob(path):
            #extracting output filename
            parameters = text + file + ' ' + out_csv
            raster2tsv.raster2tsv(parameters)
            mainDataFrame = pd.read_csv(out_csv, header=None, sep='\t')
            mainDataFrame.columns = header
        #mainDataFrame = mainDataFrame.set_index('coordinate')
        mainDataFrame.to_csv('rawData.tsv', index=False,header=False, sep='\t')
        
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
        
        database.insertCSVFile("rawData2.tsv",' ', table)
        if os.path.exists("rawData.tsv"):
            os.remove("rawData.tsv")
        if os.path.exists("rawData2.tsv"):
            os.remove("rawData2.tsv")
        
    def deleteTable(tableName):
        """
        Delete a table from the database

        :param tableName: name of the table
        """
        delete_table = "drop table " + tableName + ";"
        database.curr.execute(delete_table)
        database.conn.commit()
        print('table deleted')
        
    def cloneTable(tableName, cloneTableName):
        """
        Clone a table from the database

        :param tableName: name of the table
        :param cloneTableName: name of the cloned table
        """
        clone_table = "create table " + cloneTableName + " as (select * from " + tableName + ");"
        database.curr.execute(clone_table)
        database.conn.commit()
        print('table cloned')
        
    def changeTableName(tableName, newTableName):
        """
        Change the name of a table in the database
        
        :param tableName: name of the table
        :param newTableName: new name of the table
        """
        changeTableName = "ALTER TABLE IF EXISTS " + tableName + " RENAME TO " + newTableName + ";"
        database.curr.execute(changeTableName)
        database.conn.commit()
        print('table name changed')
        
    def getRasterImage(tableName="",rasterFileName="rasterFile.nc", Xmin=0,Ymin=0,Xmax=0,Ymax=0,Bands="*"):
        """
        Get a raster image from the database

        :param tableName: name of the table
        :param rasterFileName: name of the raster file
        :param Xmin: minimum X coordinate
        :param Ymin: minimum Y coordinate
        :param Xmax: maximum X coordinate
        :param Ymax: maximum Y coordinate
        :param Bands: bands to be extracted
        """
        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF
        df = database.getDataframeForEnvelope(tableName, Xmin,Ymin,Xmax,Ymax,Bands)
        database.dataFrame2Raster(df, rasterFileName)
        
    def dataFrame2Raster(dataframe, rasterFileName):
        """
        Create a raster image from a dataframe

        :param dataframe: dataframe
        :param rasterFileName: name of the raster file
        """

        # check rasterFile type
        gobi = rasterFileName[-3:]
        extension = '.tif'
        
        df = dataframe
        df = df.sort_values(['y','x'], ascending=[True,True])
        df = df.reset_index()
        df = df.drop(columns=["index"])
        dblen = len(df.columns) - 1
        for i in range(1,len(df.columns)-1,1):
            obj4 = c2r.csv2raster(output_file='output'+str(i)+'.nc',dataframe=df)
            obj4.toraster()
            columnDrop = 'b' + str(i)
            df = df.drop(columns=columnDrop)
        for i in range(1,dblen):
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
        
    def getDataframeForEnvelope(tableName, Xmin,Ymin,Xmax,Ymax,Bands="*",SRID=4326):
        """
        Get a dataframe from the database for a given envelope

        :param tableName: name of the table
        :param Xmin: minimum X coordinate
        :param Ymin: minimum Y coordinate
        :param Xmax: maximum X coordinate
        :param Ymax: maximum Y coordinate
        :param Bands: bands to be extracted
        :param SRID: spatial reference ID
        """

        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF

        query = "SELECT ST_X(geog) as x, ST_Y(geog) as y, " + Bands + " FROM " + tableName + " WHERE " + tableName + ".geog && ST_MakeEnvelope(" + str(Xmin) + ',' + str(Ymin) + ',' + str(Xmax) + ',' + str(Ymax) + ");"
        dataFrameEnvelope = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameEnvelope = dataFrameEnvelope.drop(columns=["geog"])
        print('dataframe created')
        return dataFrameEnvelope

    def KNN(tableName, X,Y,k = 1000,Bands="*",SRID=4326):
        """
        Get a dataframe from the database for a point and its neighbors

        :param tableName: name of the table
        :param X: X coordinate
        :param Y: Y coordinate
        :param k: number of neighbours
        :param Bands: bands to be extracted
        :param SRID: spatial reference ID
        """
        query = "SELECT ST_X(geom::geometry) as x, ST_Y(geom::geometry) as y, "+ str(Bands) + " FROM " + str(tableName) + " ORDER BY " + str(tableName) + ".geom <-> 'SRID=" + str(SRID) + ";POINT(" + str(X) + ' ' + str(Y) + ")'::geometry limit " + str(k) + ";"
        dataFrameKNN = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameKNN = dataFrameKNN.drop(columns=["geom"])
        print('dataframe created')
        return dataFrameKNN
    
    def getRasterImageKNN(tableName,rasterFileName="rasterFile.nc", X=0, Y=0,k=1000,Bands="*"):
        """
        Get a raster image from the database for a point and its neighbors

        :param tableName: name of the table
        :param rasterFileName: name of the raster file
        :param X: X coordinate
        :param Y: Y coordinate
        :param k: number of neighbours
        :param Bands: bands to be extracted
        """
        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF
        df = database.KNN(tableName, X, Y, k,Bands)
        database.dataFrame2Raster(df, rasterFileName)

    