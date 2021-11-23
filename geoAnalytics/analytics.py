import os
import subprocess
import psycopg2
import pandas as pd
from config import config

class analytics:
                    
    def KNN(tableName, X,Y,Bands,k = 1000,SRID=4326):
        conn = None
        try:
            # read database configuration
            params = config()
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**params)
            # create a new cursor
            cur = conn.cursor()
            query = "SELECT "+ Bands + " FROM " + tableName + " ORDER BY " + tableName + ".geom <-> 'SRID=" + str(SRID) + ";POINT(" + str(X) + ' ' + str(Y) + ")'::geometry limit" + str(k) + ";"
            dataFrameKNN = pd.read_sql_query(query, conn)
            return dataFrameKNN
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()