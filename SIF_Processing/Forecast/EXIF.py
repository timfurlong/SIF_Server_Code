from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

import sys

'''Module to deal with EXIF metadata'''

class EXIF:
    def __init__(self, filename):
        self.image = Image.open( filename )
        self.exif_data = self.get_exif_data( self.image )

    def get_exif_data(self, image):
        """Returns a dictionary from the exif data of an PIL Image item.
           Also converts the GPS Tags"""
        exif_data = {}
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for gps_tag in value:
                        sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
                        gps_data[sub_decoded] = value[gps_tag]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value

        return exif_data

    def _convert_to_degress(self, value):
        """Helper function to convert the GPS coordinates stored in the EXIF to
           degress in float format"""
        deg_num, deg_denom = value[0]
        d = float(deg_num) / float(deg_denom)

        min_num, min_denom = value[1]
        m = float(min_num) / float(min_denom)

        sec_num, sec_denom = value[1]
        s = float(sec_num) / float(sec_denom)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lon(self):
        """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
        lat = None
        lon = None

        if "GPSInfo" in self.exif_data:
            gps_info = self.exif_data["GPSInfo"]

            gps_latitude = gps_info.get("GPSLatitude")
            gps_latitude_ref = gps_info.get('GPSLatitudeRef')
            gps_longitude = gps_info.get('GPSLongitude')
            gps_longitude_ref = gps_info.get('GPSLongitudeRef')

            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = self._convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":
                    lat *= -1

                lon = self._convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lon *= -1

        return lat, lon


if __name__ == "__main__":
    # imName = 'Apr11_2013 10_38_35.jpg'
    imName = sys.argv[1]

    exif = EXIF( imName )
    print exif.get_lat_lon()