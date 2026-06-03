from geopy.geocoders import Nominatim
import geocoder

def current_location():
    try:
        location = geocoder.ip("me").latlng
        geo = Nominatim(user_agent="my_location_app")
        
        latitude = location[0]
        longitude = location[1]
        location = geo.reverse(f"{latitude}, {longitude}", zoom=10)
        
        return location.address
    except:
        return "Greenwich, London, UK"