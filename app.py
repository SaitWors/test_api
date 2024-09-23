import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

API_KEY = '804b25b9-8ecb-4d51-adfa-be933979fad0'

# Geocoding function
def geocode_address(address):
    response = requests.get(f'https://catalog.api.2gis.com/3.0/items/geocode', 
                            params={'q': address, 'fields': 'items.point', 'key': API_KEY})
    data = response.json()
    if 'result' in data and 'items' in data['result'] and len(data['result']['items']) > 0:
        point = data['result']['items'][0]['point']
        return point['lat'], point['lon']
    return None, None

# Distance calculation function
def get_distance(lat1, lon1, lat2, lon2):
    try:
        response = requests.get(f'https://catalog.api.2gis.com/3.0/transport/calculateRoute',
                                params={'key': API_KEY, 'points': f'{lon1},{lat1};{lon2},{lat2}', 'type': 'pedestrian'})
        data = response.json()
        if data['meta']['code'] == 200 and 'result' in data and 'routes' in data['result'] and len(data['result']['routes']) > 0:
            return data['result']['routes'][0]['total_distance']
    except Exception as e:
        print(f"Error getting distance: {e}")
    return None

# Route calculation function
def get_route(coordinates):
    route = []
    distances = []
    
    # Add the initial fixed address
    base_address = "ул. Нижегородская дом 50 (ТЦ ТРИ Д)"
    base_lat, base_lon = geocode_address(base_address)
    if base_lat and base_lon:
        route.append({'address': base_address, 'lat': base_lat, 'lon': base_lon})
    
    # Sort coordinates by geocoded latitude and longitude
    ordered_coordinates = sorted(coordinates, key=lambda k: (k['lat'], k['lon']))
    
    for coord in ordered_coordinates:
        route.append(coord)

    for i in range(len(route) - 1):
        dist = get_distance(route[i]['lat'], route[i]['lon'], route[i + 1]['lat'], route[i + 1]['lon'])
        distances.append(dist if dist is not None else "Distance calculation failed")

    return route, distances

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate_route', methods=['POST'])
def calculate_route_endpoint():
    data = request.json
    orders = data.get('orders', [])

    coordinates = []
    for order in orders:
        lat, lon = geocode_address(order['address'])
        if lat and lon:
            coordinates.append({'address': order['address'], 'lat': lat, 'lon': lon})
    
    route, distances = get_route(coordinates)
    return jsonify({'route': route, 'distances': distances})

if __name__ == '__main__':
    app.run(debug=True)
