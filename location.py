from geopy.geocoders import Nominatim
import geocoder

def current_location(location_type="area"):
    try:
        
        location = geocoder.ip("me").latlng
        geo = Nominatim(user_agent="my_location_app")
        
        latitude = location[0]
        longitude = location[1]
        if location_type == "area":
            location = geo.reverse(f"{latitude}, {longitude}", zoom=10)
            return location.address
        elif location_type == "coords":
            return (latitude, longitude)
    except:
        return "Greenwich, London, UK"