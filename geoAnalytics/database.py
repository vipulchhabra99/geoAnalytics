from geoAnalytics.config import config
import psycopg2
import pandas as pd
from geoAnalytics import csv2raster as c2r
import os
import subprocess

class database:
    conn = ""
    cur = ""
    def connect(dbName="", hostIP="", user="", password="", port=5432):
        if dbName != "":
            with open('database.ini',"w") as dbFile:
                buffer = "[postgresql]\nhost = " + hostIP +"\nport = " + str(port) +"\ndatabase = " + dbName +"\nuser = " + user + "\npassword = " + password
                dbFile.write(buffer)
                dbFile.close()                     
        database.testDatabaseConnection()   
    
    def disconnect():
        if database.conn is not None:
            print("Disconnecting from database")
            database.conn.close()
            print("Disconnected from database")
                             
    def testDatabaseConnection():
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
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
                         
    def createTable(tableName, totalBands):
        create_table = "create table " + tableName + "(" + totalBands + ");"
        database.curr.execute(create_table)
        database.conn.commit()
    
    def insertRasterFile(filename,seperator, tableName, scalingFactor, roundTo=5):
        with open(filename) as inFile:
            with open("temp_" + filename,"w") as tempFile:
                for lines in inFile:
                    word = lines.strip()
                    word = word.split("\t")

                    for w in word:
                        w = str(round(float(w) *scalingFactor, roundTo))
                        sqlLine +=  w + " "
                    sqlLine += "\n"
                    tempFile.write(sqlLine)
                tempFile.close()
            inFile.close()
                         
        copy_file = "copy " + tableName + " from '" + "temp_" + filename + "' delimiters '" + ' ' + "' csv;"
        database.curr.execute(copy_file)

        # finished
        database.conn.commit()
        
        if os.path.exists("temp_" + filename):
            os.remove("temp_" + filename)
        
    def deleteTable(tableName):
        delete_table = "delete table " + tableName + ";"
        database.curr.execute(delete_table)
        database.conn.commit()
        
    def cloneTable(tableName, cloneTableName):
        clone_table = "create table " + cloneTableName + "as (select * from " + tableName + ");"
        database.curr.execute(clone_table)
        database.conn.commit()
        
    def changeTableName(tableName, newTableName):
        changeTableName = "ALTER TABLE IF EXISTS " + tableName + " RENAME TO " + newTableName + ";"
        database.curr.execute(changeTableName)
        database.conn.commit()
        
        
    def getRasterImage(tableName="",rasterFileName="rasterFile.nc", Xmin=0,Ymin=0,Xmax=0,Ymax=0,Bands="*"):
        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF
        df = database.getDataframeForEnvelope(tableName, Xmin,Ymin,Xmax,Ymax,Bands)
        database.dataFrame2Raster(df, rasterFileName)
        
    def dataFrame2Raster(dataframe, rasterFileName):
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
        
        buffer = 'cdo cat output*.nc ' + rasterFileName
        subprocess.getstatusoutput(buffer)
        args = ('rm', 'output*.nc')
        subprocess.call('%s %s' % args, shell=True)

    def getDataframeForEnvelope(tableName, Xmin,Ymin,Xmax,Ymax,Bands="*",SRID=4326):
        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF

        query = "SELECT ST_X(geom) as x, ST_Y(geom) as y, " + Bands + " FROM " + tableName + " WHERE " + tableName + ".geom && ST_MakeEnvelope(" + str(Xmin) + ',' + str(Ymin) + ',' + str(Xmax) + ',' + str(Ymax) + ");"
        dataFrameEnvelope = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameEnvelope = dataFrameEnvelope.drop(columns=["geom","filename"])
        return dataFrameEnvelope

    def KNN(tableName, X,Y,k = 1000,Bands="*",SRID=4326):
        query = "SELECT ST_X(geom) as x, ST_Y(geom) as y, "+ str(Bands) + " FROM " + str(tableName) + " ORDER BY " + str(tableName) + ".geom <-> 'SRID=" + str(SRID) + ";POINT(" + str(X) + ' ' + str(Y) + ")'::geometry limit " + str(k) + ";"
        dataFrameKNN = pd.read_sql_query(query, database.conn)
        if Bands == "*":
            dataFrameKNN = dataFrameKNN.drop(columns=["geom","filename"])
        return dataFrameKNN
    
    def getRasterImageKNN(tableName,rasterFileName="rasterFile.nc", X=0, Y=0,k=1000,Bands="*"):
        # connect to database
        #create geoTIFF file
        #gDal transform to geoTIFF
        df = database.KNN(tableName, X, Y, k,Bands)
        database.dataFrame2Raster(df, rasterFileName)

    