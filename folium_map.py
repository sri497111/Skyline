import folium

def create_folium_map(coords, zoom=13):
    lat = coords[0]
    lon = coords[1]
    
    fmap = folium.Map(location=(lat, lon), zoom_start=zoom)
    
    return fmap

def overlay_tiles(coords, key, typeofmap="full"):
    if typeofmap == "full":
        tile_map = create_folium_map((coords[0], coords[1]))
    elif typeofmap == "preview":
        tile_map = create_folium_map((coords[0], coords[1]), 10)
    
    types = [
        {'type': "precipitation_new", 'name': "Precipitation", 'active': True},
        {'type': "temp_new", 'name': "Temperature", 'active': False},
        {'type': "wind_new", 'name': "Wind", 'active': False},
        {'type': "clouds_new", 'name': "Clouds", 'active': False}
    ]
    
    if typeofmap == "full":
        for t in types:
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/{t['type']}/{{z}}/{{x}}/{{y}}.png?appid={key}",
                attr="© OpenWeatherMap",
                name=t['name'],
                overlay=True,
                control=True,
                opacity=2,
                show=t['active']
            ).add_to(tile_map)
    elif typeofmap == "preview":
        for t in types:
            folium.TileLayer(
                tiles=f"https://tile.openweathermap.org/map/{t['type']}/{{z}}/{{x}}/{{y}}.png?appid={key}",
                attr="© OpenWeatherMap",
                name=t['name'],
                overlay=False,
                control=False,
                opacity=2,
                show=t['active']
            ).add_to(tile_map)
    
    folium.LayerControl(collapsed=False).add_to(tile_map)
    
    tile_map.save(f"./map.html")



