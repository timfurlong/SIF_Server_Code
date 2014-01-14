import math

def lat_long_box(latitude, longitude):
	dx = 557.14/2
	dy = 378.57/2
	dlat = change_lat(dy)
	dlong = change_long(latitude, dx)
	north = latitude+abs(dlat)
	south = latitude-abs(dlat)
	east = longitude-abs(dlat)
	west = longitude+abs(dlat)

	return [north, south, east, west]


def change_coord(latitude,longitude,vector,dt):
	latitude = float(latitude)
	longitude = float(longitude)
	meterPerPixel = 0.8286
	dx = float(vector[3])-float(vector[1]) #in pixels
	dy = float(vector[4])-float(vector[2]) #in pixels

	meterdx = dx*meterPerPixel
	meterdy = dy*meterPerPixel

	newLat = latitude+change_lat(dx)*(dt*2) # dt is in minutes
	newLong = longitude+change_long(latitude, dy)*(dt*2) #dt is in minutes

	return [newLat, newLong]

def change_lat(dmeters):
	earthRadius = 6731000 #in meters
	ans = (dmeters/earthRadius)*(180/math.pi)
	return ans


def change_long(latitude, dmeters):
	earthRadius = 6731000 #in meters
	ans = (dmeters/(earthRadius*math.cos(latitude*math.pi/180)))*(180/math.pi)
	return ans

def update_kml(north, south, east, west):
	kmlfile = 'test.kml'
	forecastfolder = 'Current'
	imgfile = '07_1_0627_forecast.jpg'
	fid = open(kmlfile, 'w')
	fid.write('<kml>\n')
	fid.write('<Folder>\n<name>' + forecastfolder + '</name>\n')
	#for images in forcasefoler
	fid.write('<GroundOverlay>\n');
	fid.write('    <Icon>\n');
	fid.write('        <href>' + imgfile + '</href>\n');
	fid.write('    </Icon>\n');
	fid.write('    <LatLonBox>\n');
	fid.write('        <north>' + repr(north) + '</north>\n');
	fid.write('        <south>' + repr(south) + '</south>\n');
	fid.write('        <east>' + repr(east) + '</east>\n');
	fid.write('        <west>' + repr(west) + '</west>\n');
	fid.write('        <rotation>' + repr(90)+'</rotation>\n');
	fid.write('    </LatLonBox>\n');
	fid.write('</GroundOverlay>\n');
	#end for loop
	fid.write('</Folder>\n');
	fid.write('</kml>');
	fid.close();


lat_test = 40.0037861
long_test = -105.2640917

vector = ['sensorId','1.7013059e+02',   '2.3681256e+02',   '1.6235475e+02',   '2.8137290e+02']
dt = 30;

[new_lat_test, new_long_test] = change_coord(lat_test, long_test, vector, dt)
print(new_lat_test, new_long_test)
[north, south, east, west] = lat_long_box(new_lat_test, new_long_test)
print(north,south,east,west)
update_kml(north,south,east,west)



