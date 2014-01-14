# -*- coding: utf-8 -*-
'''
@author:    Tim Furlong
@summary:   This module contains all of the functionality of the socket server.
            It creates the server, handles connections, downloads images,
            and adds them to the queue appropriately.
'''

# Standard python libraries
import socket
import datetime
import sys
import os
import time
from binascii import hexlify # To decode hex values
from math import floor
import logging

# 3rd Party libraries
import eventlet # http://eventlet.net

sys.path.append('.')
sys.path.append('..')

# Imports of code written for this project
from DBManager import DB # Capstone database manager
from rsync import rsync

class sockServer:

   # Constants
   PORT              = 5000  # Arbitrary non-privileged port
   # 'Shared secret' code at the beginning of each message for a crude attempt at security
   MESSAGE_SIGNATURE = 'cachemoney'

   BUFF_SIZE     = 512
   MIN_PIC_LINES = 50

   '''The various directories which comprise our file system based processing queue.'''
   OUTPUT_DIR      = 'outputFiles'
   UNPROCESSED_DIR = os.path.join( OUTPUT_DIR, 'Unprocessed' )
   PROCESSED_DIR   = os.path.join( OUTPUT_DIR, 'Processed' )
   PROCESSING_DIR  = os.path.join( OUTPUT_DIR, 'Processing' )

   OUTPUT_EXT      = 'jpg'

   def __init__(self, debug=False):
      self.debug  = debug # Set debug mode
      if self.debug:
         logLevel = logging.DEBUG
      else:
         logLevel = logging.INFO
      # Set logging level
      logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)

      if not os.path.isdir(self.OUTPUT_DIR):
         os.mkdir(self.OUTPUT_DIR)
      if not os.path.isdir(self.UNPROCESSED_DIR):
         os.mkdir(self.UNPROCESSED_DIR)
      if not os.path.isdir(self.PROCESSED_DIR):
         os.mkdir(self.PROCESSED_DIR)
      if not os.path.isdir(self.PROCESSING_DIR):
         os.mkdir(self.PROCESSING_DIR)
      self.db = DB(debug = self.debug)
      self.rsync = rsync( self.debug )

      if socket.gethostname() == 'cet-sif':
         self.OnServer = True
         self.host     = '128.138.248.205' # Static ip resolution of cet-sif.colorado.edu
      else:
         self.OnServer = False
         self.host     = socket.gethostbyname(socket.gethostname()) # Set to localhost

   def runNonBlockingSocket(self):
      '''Run the nonblocking socket server. Any time a client connects to
      (self.host, self.PORT), recieveData is called to handle the request.'''

      listener = eventlet.listen( (self.host, self.PORT)  )
      logging.info( 'Recieving on %s, %s' % (self.host, self.PORT) )
      eventlet.serve(listener, self.recieveData)

   def recieveData(self, client_sock, client_addr):
      '''Callback function for every time a client connects to the nonblocking socket'''

      logging.info( "client connected", client_addr )
      first = True
      lines = []

      '''Collect all of the incoming data lines, each of size <BUFF_SIZE>.'''
      while 1:
         line = client_sock.recv( self.BUFF_SIZE )
         if first:
            tic = time.time()
            first = False
         if not line:
            break
         lines.append(line)

      '''Check the validity of the message. Message cannot be empty, and must contain
      <MESSAGE_SIGNATURE> in the correct place for us to process the information
      contained within the received lines'''
      if len(lines) == 0:
         logging.info('No message provided. Ignoring client.')
         return
      # Check signature and get image file name
      if len(lines[0].split('\n')) < 2:
         logging.info('Incoming message is not the required format. Ignoring client.')
         return # ignore this message
      signature, imageName = tuple( lines[0].split('\n')[0:2] )
      if self.MESSAGE_SIGNATURE != signature:
         logging.info('Illegal message recieved with signature:\n%s' % lines[0])
         return # ignore this message
      lines[0] = ''.join( lines[0].split('%s\n' % imageName)[1:] )
      cameraID, timeTaken, lat, lon, powerData = tuple( imageName.split('_') )

      # Detect datatype of message, and process accordingly.
      if len(lines) > self.MIN_PIC_LINES:
         # Message is a picture
         lat       = float( lat.replace(',','.') )
         lon       = float( lon.replace(',','.') )
         timeTaken = time.strptime( timeTaken, '%H%M%S')
         groupID   = self.timeToGroupID( timeTaken )

         self.db.setCameraGeoTag(cameraID, lat, lon)

         imPath = self.saveImg(lines, groupID)
         if self.OnServer:
            self.rsync.sendPhotoToCETResearch( os.path.dirname(imPath), verbose=False )
         logging.debug('Image added to queue')
      else:
         # Message is a power reading
         temp  = hexlify(lines[0][0])+hexlify(lines[0][1])+hexlify(lines[0][2])
         temp  = int(temp,16)<<1
         value = float(temp)/((2**24) -1)
         value = (value/0.36)*60
         logging.debug( 'Power=%f retrieved' % value )
         self.db.writePowerData( value, 'TEST_GEOTAG', datetime.datetime.now() )
         logging.debug('Power data written to database')
         self.db.syncPowerWithCETResearch(verbose=False)
      logging.debug( 'Total time taken = %f' % (time.time()-tic) )

   def groupIDtoDatetime( self, groupID ):
      '''Convert a groupID to datetime. Note that groupID's are incremented
      every 30 seconds, starting at midnight (groupID = 0)'''

      today    = datetime.date.today()
      midnight = datetime.datetime(year=today.year, month=today.month, day=today.day,
                          hour=0, minute=0, second=0)
      thirtySec = datetime.timedelta(seconds=30)
      return midnight + (groupID * thirtySec)

   def timeToGroupID( self, t ):
      '''Convert a datetime to groupID. Note that groupID's are incremented
      every 30 seconds, starting at midnight (groupID = 0)'''
      return int( 120 * t.tm_hour + 2 * t.tm_min + floor(t.tm_sec/30) )

   def saveImg(self, dataLines, groupID):
      '''Save an image and place it at back of queue (Unprocessed directory).'''
      idealDateTimeTaken = self.groupIDtoDatetime( groupID )
      timeStr            = idealDateTimeTaken.strftime("%h%d_%Y-%H_%M_%S")
      now                = datetime.datetime.now()
      nowStr             = now.strftime("%h%d_%Y %H_%M_%S")

      outputFileDir = os.path.join( self.UNPROCESSED_DIR,
                                    '%i-%s' % (groupID,timeStr) )
      if os.path.isdir(outputFileDir) is False:
         os.mkdir( outputFileDir )
      outputFilePath = os.path.join( outputFileDir,
                                     '%s.%s' % (nowStr,self.OUTPUT_EXT) )
      f = open(outputFilePath, 'w')
      for line in dataLines:
         f.write( line )
      f.close()

      logging.info('%s written successfully' % outputFilePath)

      return outputFilePath

   def runSocket(self,customHostPort=None):
      '''Run a socket. This implementation is blocking.'''

      if customHostPort:
         host, port = customHostPort
      else:
         host, port = self.host, self.PORT
      self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.sock.bind((host, port))
      self.sock.listen(1)
      self.conn, self.addr = self.sock.accept()

      logging.debug( 'Connected by %s' % (self.addr,) )

   def recieveOne(self):
      '''Recieve one image, and save it using saveImg. Then we close the program'''
      self.runSocket()
      lines = []
      first = True
      while 1:
         line = self.conn.recv( self.BUFF_SIZE )
         if first:
            tic = time.time()
            first = False
         lines.append( line )
         if not line:
            break
      self.saveImg(lines)
      logging.info( 'Total time taken = %f' % (time.time()-tic) )
      self.conn.close()
      exit()

   def keepRecievingStrs(self):
      '''Keep recieving strings, and keep incrementing the lines array'''
      lines = []
      while 1:
         self.runSocket()
         try:
            while 1:
               line = self.conn.recv( self.BUFF_SIZE )
               if not line:
                  break
               lines.append(line)
         except socket.error, e:
            logging.error( e )
         if len(lines) == 1:
            logging.debug(lines[0])
         else:
            logging.debug('%d lines received' % len(lines))
         self.conn.close()
         self.runSocket()

if __name__ == '__main__':
   '''If the debug argument is provided, we will set out logging level to debug.'''
   debug = False
   if 'debug' in sys.argv:
      debug = True
   print 'DEBUG MODE = %s' % debug
   server = sockServer(debug=debug)
   server.runNonBlockingSocket()
