'''
@author:    Tim Furlong
@summary:   Database module to facilitate interaction with the SQLite database.
'''

import sqlite3
import os
import datetime
import shutil
import sys
from pprint import pprint
import logging

class DB:
   '''This module controls all interaction with the SQLite database.'''

   DB_PATH = 'CapstoneDatabase.db' # Relative to project root

   def __init__(self, debug=False):
      self.debug  = debug # Set debug mode
      if self.debug:
         logLevel = logging.DEBUG
      else:
         logLevel = logging.INFO
      # Set logging level
      logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)

   def dict_factory(self, cursor, row):
      '''Helper function that allows us to retrieve database rows as dictionaries'''
      d = {}
      for idx, col in enumerate(cursor.description):
         d[col[0]] = row[idx]
      return d

   def completeImageMove(self, f, loc):
      '''Move the file f to the location loc.
      This method effictivly avoids all of the common IOErrors seen by file directory
      operations though a whole bunch of use case checking.'''

      getDirName = lambda x: os.path.basename( os.path.dirname( x ) )

      if os.path.isfile(f):
         if os.path.isfile(loc) is False:
            shutil.move(f, loc)
         else:
            logging.debug('Replacing:\n\t%s\nwith\n\t%s' % (loc,f,) )
            os.remove( loc )
            shutil.move(f,loc)
      else:
         if os.path.isfile(loc):
            logging.info('%s already exists in %s'%(os.path.basename(f),getDirName(loc)))
         else:
            logging.info('%s does not exist in either %s or %s\n' % (os.path.basename(f), getDirName(f), getDirName(loc) ))
            raise

   def convertSQLiteDateTime(self, dt):
      '''converts a SQLite formatted datetime (e.g. u'2013-02-27 12:57:33.759096')
      to a python datetime object'''
      date, time           = tuple( dt.split(' ') )
      year, month, day     = tuple( date.split('-') )
      hour, minute, second = tuple( time.split(':') )
      second, ms           = tuple( second.split('.') )

      year=int(year); month=int(month); day=int(day);
      hour=int(hour); minute=int(minute); second=int(second); ms=int(ms)

      return datetime.datetime( year, month, day, hour, minute, second, ms )

   def printTableData(self, tableName, ids=None):
      '''Print rows from a DB table specified by tableName. If the ids parameter is given,
      only rows with matching ids will be printed.'''

      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      conn.row_factory = self.dict_factory

      c = conn.cursor()
      if ids==None:
         c.execute("SELECT * FROM %s;" % tableName ) # Cannot use ? for column or table names
         data = c.fetchall()
         print '# of rows = %d' % len(data)
      else:
         if type(ids) is not list:
            ids = [ids]
         ids = [str(ID) for ID in ids]
         idsStr = ','.join(ids)
         c.execute("SELECT * FROM %s WHERE id in (?);" % tableName,(idsStr,) )
         data = c.fetchone()
      pprint( data )

      conn.close()

   def garbageCollector(self, tableName):
      '''Cleans old data in <tablename>. Can be called periodically.'''

      oldDataDate = datetime.datetime.now() - datetime.timedelta(days=1)
      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      c = conn.cursor()
      q = "DELETE FROM %s " % tableName
      c.execute(q + "WHERE time < ?", (oldDataDate,) )
      conn.commit()
      conn.close()

   def createTables(self, tableNums = [1,2,3,4,5,6]):
      '''Create all the tables indicated by the input tableNums. The table
      enumeration is defined below:
         1) MotionVectors
         2) StitchedImages
         3) cameras
         4) ongridSensors
         5) ProcessingQueue
         6) PowerData
      '''
      if type(tableNums) is not list:
         tableNums = [tableNums]

      for entry in tableNums:
         if entry not in [1,2,3,4,5,6]:
            logging.info('tableNums entry %d is not a valid tableNum' % entry)
            raise

      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      c = conn.cursor()
      for entry in tableNums:
         if entry == 1:
            c.execute("""CREATE TABLE MotionVectors
                        (id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL  UNIQUE,
                        time TIMESTAMP, camera_id NUMERIC,
                        relX1 NUMERIC, relY1 NUMERIC,
                        relX2 NUMERIC, relY2 NUMERIC,
                        magX NUMERIC, magY NUMERIC);
                     """)
         elif entry == 2:
            c.execute("""CREATE TABLE StitchedImages
                        (id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL  UNIQUE,
                        time TIMESTAMP, image BLOB);
                     """)
         elif entry == 3:
            c.execute("""CREATE TABLE cameras
                        (id INTEGER PRIMARY KEY  NOT NULL ,
                        geotag TEXT,
                        sensorID VARCHAR DEFAULT (0) )""")
         elif entry == 4:
            c.execute("""CREATE TABLE ongridSensors
                        (id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL  UNIQUE,
                        geotag TEXT);
                     """)
         elif entry == 5:
            c.execute("""CREATE TABLE ProcessingQueue
                        (id INTEGER PRIMARY KEY  NOT NULL ,
                        processed BOOL NOT NULL  DEFAULT (0) ,
                        groupID INTEGER NOT NULL ,
                        last_updated DATETIME NOT NULL  DEFAULT (CURRENT_TIMESTAMP) ,
                        num_images INTEGER NOT NULL  DEFAULT (0) ,
                        image_paths TEXT NOT NULL )
                     """)
         elif entry == 6:
            c.execute("""CREATE TABLE PowerData
                        (id INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE ,
                        time DATETIME NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                        geotag TEXT NOT NULL ,
                        power NUMERIC NOT NULL )
               """)
         else:
            logging.info('''tableNums entry %d is not a valid tableNum
                        (and somehow bypassed inital check!)''' % entry)
            raise

      conn.commit()
      conn.close()

   # =======================================
   # ========= DB Read methods =============
   # =======================================
   def getCameraGeoTag(self, sensorID):
      conn = sqlite3.connect( self.DB_PATH,
                        detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      conn.row_factory = self.dict_factory
      c = conn.cursor()
      c.execute('''SELECT geotag FROM cameras WHERE sensorID=?''', (sensorID,))
      row = c.fetchone()
      conn.close()

      if row is None:
         logging.error('Cannot get geotag: sensorID=%d not found in database')
         sys.exit(1)

      return row['geotag']

   # =======================================
   # ======== DB Write methods =============
   # =======================================
   def setCameraGeoTag(self, sensorID, lat, lon):
      geotag = '%s,%s' % (lat,lon)
      conn = sqlite3.connect( self.DB_PATH,
                        detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      conn.row_factory = self.dict_factory
      c = conn.cursor()
      c.execute('''SELECT id FROM cameras WHERE sensorID=?''', (sensorID,))
      row = c.fetchone()
      if row == None:
         c.execute('''INSERT INTO cameras
                      (sensorID, geotag)
                      VALUES (?,?)''', (sensorID, geotag))
      else:
         c.execute("UPDATE cameras SET geotag=? WHERE id=?", (geotag,row['id']))
      conn.commit()
      conn.close()


   def addToQueue(self, groupID, imagePath):
      '''Outdated. Queue no longer exists in database'''

      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      conn.row_factory = self.dict_factory
      c = conn.cursor()

      '''If row with groupID already exists, read it's contents so that we can
      decide whether to insert a new row or update it's values accordingly'''
      c.execute('''SELECT id, processed, groupID,
                   last_updated as "last_updated [timestamp]", num_images, image_paths
                   FROM ProcessingQueue
                   WHERE groupID=?''', (groupID,))
      row = c.fetchone()
      if row == None:
         # First image of the set => Make a new row.
         c.execute("""INSERT INTO ProcessingQueue
                     (processed, groupID, last_updated, num_images, image_paths)
                     VALUES (?,?,?,?,?)
                  """ , (0, groupID, datetime.datetime.now(), 1, '[%s]'%imagePath,) )
         conn.commit()
      else:
         # At least one image from set has already arrived. Update the row.
         self.printTableData('ProcessingQueue', ids=row['id'])

         # Get current image paths (as string), then add new image path
         imagePaths = row['image_paths']
         imagePaths = imagePaths.replace(']',', %s]' % imagePath)

         c.execute('''UPDATE ProcessingQueue
                      SET last_updated=?,num_images=?,
                          image_paths=?, processed=?
                      WHERE id=?''',
                 (datetime.datetime.now(), row['num_images']+1,
                  imagePaths, 0,
                  row['id'],) )
         conn.commit()
         self.printTableData('ProcessingQueue', row['id'])


      conn.close()

   def setProcessedFlag(self, queueId, processed=1):
      '''Outdated. ProcessingQueue is no longer in DB.'''
      conn = sqlite3.connect( self.DB_PATH )
      c = conn.cursor()
      c.execute("UPDATE ProcessingQueue SET processed=? WHERE id=?", (processed,queueId))
      conn.commit()
      conn.close()

   def setPicGroupPaths(self, queueId, paths):
      '''Outdated. ProcessingQueue no longer in DB'''
      conn = sqlite3.connect( self.DB_PATH )
      c = conn.cursor()
      c.execute("UPDATE ProcessingQueue SET image_paths=? WHERE id=?", (str(paths),queueId))
      conn.commit()
      conn.close()

   def writePowerData(self, power, geotag, timetag):
      # The detect_types keyword param tells sqlite to convert datetime objs automatically
      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      c = conn.cursor()

      # (id INTEGER, time TEXT ,
      #  geotag TEXT , power NUMERIC)
      c.execute(
            """INSERT INTO PowerData (power, time, geotag)
               VALUES (?,?,?)
               """ , (power, timetag, geotag) )
      conn.commit()
      conn.close()

   def addCamera(self, geotag):
      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      c = conn.cursor()

      c.execute(
            """INSERT INTO cameras(geotag)
               VALUES (?)
               """ , (geotag,) )

      conn.commit()
      conn.close()

   def addOnGridSensor(self, geotag):
      conn = sqlite3.connect( self.DB_PATH,
                     detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
      c = conn.cursor()

      c.execute(
            """INSERT INTO ongridSensors(geotag)
               VALUES (?)
               """ , (geotag,) )

      conn.commit()
      conn.close()

      '''Below are functions pertaining to the database implementation of the queue.
      Currently, the queue is implented as part of the filesystem, but changing to
      a database implementation would be easy using the below functions.'''
      def getUnprocessedQueueItems(self):
         '''Get all queue items with processed=0, and order them by last_updated'''

         conn = sqlite3.connect( self.DB_PATH,
                        detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
         conn.row_factory = self.dict_factory

         c = conn.cursor()
         c.execute("""SELECT * FROM ProcessingQueue
                      WHERE processed = 0
                      ORDER BY last_updated;
                  """ )
         data = c.fetchall()
         conn.close()
         return data

      def getQueueItems(self):
         '''Get all queue items with processed=0, and order them by last_updated'''
         conn = sqlite3.connect( self.DB_PATH,
                        detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
         conn.row_factory = self.dict_factory

         c = conn.cursor()
         c.execute("""SELECT * FROM ProcessingQueue
                      ORDER BY last_updated;
                  """ )
         data = c.fetchall()
         conn.close()
         return data


if __name__ == '__main__':
   '''DBManager.py is never called directly, and so the below code is never called.
   So it is safe to assume that when we do call it directly, we want debug mode to be on. '''

   db = DB(debug=True)





