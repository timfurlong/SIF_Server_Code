'''
@author:    Tim Furlong and Cole Duclos
@summary:   Module to generate our KML forcast files from the template
            defined by KMLtemplate.tmpl
'''
from Cheetah.Template import Template # Our templating engine
import os
import sys
sys.path.append('Matlab')
sys.path.append('.')
sys.path.append('Forecast')
import math
from copy import copy # To override pythons default assignment by pointers behavior
import logging
from DBManager import DB

forecastIntervals = [0,1,5,10,15,30,60]
# Field of view
FOV_dx = 557.14/2
FOV_dy = 378.57/2

class kmlMaker:

   public_url = 'http://cet.colorado.edu/~sif/Forecast/ForecastOutput'
   def __init__(self, debug=False):
      self.debug  = debug # Set debug mode
      if self.debug:
         logLevel = logging.DEBUG
      else:
         logLevel = logging.INFO
      # Set logging level
      logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)
      self.db = DB(self.debug)

   '''=======  Helper functions  ========'''

   def _change_lat(self, dmeters):
      earthRadius = 6731000 #in meters
      ans = (dmeters/earthRadius)*(180/math.pi)
      return ans


   def _change_long(self, latitude, dmeters):
      earthRadius = 6731000 #in meters
      ans = (dmeters/(earthRadius*math.cos(latitude*math.pi/180)))*(180/math.pi)
      return ans

   def _getVectors(self, vectorFile ):
      '''Open <vectorFile> and return the rows as a dictionary with
      structure: 'id': (lat1, lon1, lat2, lon2)'''

      vectorFile = open( vectorFile, 'r' )
      vectors = {}
      for line in vectorFile:
         v = line.split('   ')
         ID = v[1].split('.')[0]
         vectors[ID] = ( float(v[2]), float(v[3]), float(v[4]), float(v[5]) )
      return vectors

   def lat_long_box(self, latitude, longitude):
      '''Calculate the box that Google Earth needs to use as the location for the
      image overlay.'''

      dlat  = self._change_lat(FOV_dy)
      dlong = self._change_long(latitude, FOV_dx)
      north = latitude+abs(dlong)
      south = latitude-abs(dlong)
      east  = longitude+abs(dlat)
      west  = longitude-abs(dlat)

      return [north, south, east, west]


   def change_coord(self, latitude,longitude,vector,dt):
      '''Calculate where the point located at <latitude>,<longitude> will be
      located <dt> minutes from now given the motion defined by <vector>.'''

      latitude = float(latitude)
      longitude = float(longitude)
      meterPerPixel = 0.8286
      dx = float(vector[2])-float(vector[0]) #in pixels
      dy = float(vector[3])-float(vector[1]) #in pixels

      meterdx = dx*meterPerPixel
      meterdy = dy*meterPerPixel

      newLat = latitude+self._change_lat(meterdx)*(dt*2) # dt is in minutes
      newLong = longitude+self._change_long(latitude, meterdy)*(dt*2) #dt is in minutes

      return newLat, newLong

   '''
   ===================================
   The primary method of the kml class
   ===================================
   '''
   def createKML( self, vectorDir,forecastImageDir, kmloutDir):
      ''' Create a KML forecast using the vector file contained in
      <vectorDir> and the images contained within <forecastImageDir>.
      The forecast will be put into <kmloutDir>.
      '''

      vectorFile = [f for f in os.listdir(vectorDir) if 'vectors' in f][0]
      print vectorFile,forecastImageDir
      vectorFile = os.path.join(vectorDir, vectorFile)
      vectors = self._getVectors(vectorFile)

      imagePaths = [os.path.join(forecastImageDir, f) for f in os.listdir(forecastImageDir)
                                               if f.endswith('.jpg')]
      images = []
      for p in imagePaths:
         name = os.path.basename(p)
         sensorID = name.split('_')[1]
         motionVec = vectors[ sensorID ]

         geotag = self.db.getCameraGeoTag( sensorID )
         lat, lon = (float(x) for x in geotag.split(','))

         rotation = 90
         image_info = {
            'publicpath':'%s/%s' % (self.public_url,name),
            'name': name,
            'path': p,
            'sensorID': sensorID,
            'vector': motionVec,
            'lat': lat,
            'lon': lon,
            'rotation': rotation
         }
         images.append( image_info )

      intervals = {}
      for dt in forecastIntervals:
         intervals[dt] = []
         for im in images:
            p = copy(im)
            p['new_lat'],p['new_lon'] = self.change_coord(im['lat'], im['lon'], im['vector'], dt)
            p['box'] = self.lat_long_box(p['new_lat'], p['new_lon'])
            intervals[dt].append( p )
      namespace = {
         'forecastfolder': 'Cloud Forecasts',
         'intervals': intervals,
      }
      '''Open template and fill the place holders according to the dictionary <namespace>'''
      t = Template(file='Forecast/KMLtemplate.tmpl', searchList=[namespace])

      kmlFile = os.path.join( kmloutDir, 'forecast.kml') # Output kml file
      kmlFile = open(kmlFile, 'w')
      kmlFile.write( str(t) ) # Write the filled template file to <kmlFile>
      kmlFile.close()


