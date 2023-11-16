from flask import Flask, request, render_template, jsonify
from zeep import Client
import requests
import json
from geopy.distance import great_circle
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

################################################################################################
########################################### API REST ###########################################
################################################################################################

OPEN_ROUTE_API_KEY = "5b3ce3597851110001cf62486fe955f9f0044f578dcd9d175421f164"
BORNES_API_URL = "https://odre.opendatasoft.com/explore/dataset/bornes-irve/api/?disjunctive.region&disjunctive.departement"

""" class Cartographie(Resource):
    def get(self, start, end):
        url = f"https://api.openrouteservice.org/v2/directions/driving-car?start={start}&end={end}"
        headers = {"Authorization": OPEN_ROUTE_API_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()
        distance = data["features"][0]["properties"]["segments"][0]["distance"]
        return {"distance": distance}
 """        

class Cartographie(Resource):
    def get(self, start, end):
        url = f"https://api.openrouteservice.org/v2/directions/driving-car?start={start}&end={end}"
        headers = {"Authorization": OPEN_ROUTE_API_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()

        # Print the data structure to inspect it
        print("inspection du format data /n")
        print(data)

        # Now try to access the distance
        try:
            distance = data["features"][0]["properties"]["segments"][0]["distance"]
            print(distance)
            return {"distance": distance}
        except KeyError as e:
            print(f"KeyError: {e} not found in data.")
            return {"error": "Invalid data structure"}


class BornesRecharge(Resource):
    def get(self, lat, lon):
        url = BORNES_API_URL + f"{lat},{lon},10000"  # Cherche les bornes dans un rayon de 10 km
        response = requests.get(url)
        data = response.json()
        bornes = [{"nom": record["fields"]["n_station"], 
                   "adresse": record["fields"]["ad_station"], 
                   "lat": record["fields"]["geom"]["coordinates"][1], 
                   "lon": record["fields"]["geom"]["coordinates"][0]} 
                  for record in data["records"]]
        return bornes
    # def get(self, lat, lon):
    #     try:
    #         # Vérifiez si la latitude et la longitude sont valides
    #         if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
    #             return {"error": "Invalid latitude or longitude"}, 400

    #         url = BORNES_API_URL + f"{lat},{lon},10000"  # Cherche les bornes dans un rayon de 10 km
    #         response = requests.get(url)

    #         # Vérifiez si la requête a réussi
    #         if response.status_code == 200:
    #             data = response.json()
    #             records = data.get('records', [])  # obtenir la liste des enregistrements

    #             bornes = [
    #                 {
    #                     "nom": record.get("fields", {}).get("n_station", "N/A"), 
    #                     "adresse": record.get("fields", {}).get("ad_station", "N/A"), 
    #                     "lat": record.get("fields", {}).get("geom", {}).get("coordinates", [None, None])[1], 
    #                     "lon": record.get("fields", {}).get("geom", {}).get("coordinates", [None, None])[0]
    #                 } for record in records
    #             ]

    #             return bornes, 200  # le code de statut HTTP pour une réponse réussie
    #         else:
    #             return {"error": "API request failed with status code " + str(response.status_code)}, 500

    #     except Exception as e:
    #         return {"error": f"An unexpected error occurred: {str(e)}"}, 500

api.add_resource(Cartographie, '/cartographie/<string:start>/<string:end>')
api.add_resource(BornesRecharge, '/bornes/<float:lat>/<float:lon>')

################################################################################################
########################################### API REST ###########################################
################################################################################################

WSDL_URL = "http://127.0.0.1:8000/?wsdl"
client = Client(WSDL_URL)

REST_ENDPOINT = "http://localhost:5000"  # URL de base du serveur REST

OPEN_ROUTE_API_KEY = "5b3ce3597851110001cf62486fe955f9f0044f578dcd9d175421f164"

BORNES_API_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/bornes-irve/records?limit=?"

def get_coordinates(address):
    """
    Récupère la latitude et la longitude pour une adresse donnée en utilisant l'API OpenRouteService.
    :param address: L'adresse complète pour laquelle la latitude et la longitude doivent être obtenues.
    :return: Un tuple (latitude, longitude) ou (None, None) si les coordonnées ne peuvent pas être trouvées.
    """
    headers = {
        'Authorization': OPEN_ROUTE_API_KEY,
    }
    # Remplacez les espaces par '+', car c'est un format commun pour les requêtes d'URL.
    formatted_address = address.replace(' ', '+')
    url = f"https://api.openrouteservice.org/geocode/search?text={address}, France&size=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200 and response.json()['features']:
        coords = response.json()['features'][0]['geometry']['coordinates']
        # Les coordonnées sont retournées dans l'ordre [longitude, latitude].
        return coords[1], coords[0]
    else:
        # Si la réponse n'est pas réussie ou qu'aucune feature n'est trouvée, retournez None pour les deux.
        return None, None


def get_route(start_coords, end_coords):
    headers = {
        'Authorization': '5b3ce3597851110001cf62486fe955f9f0044f578dcd9d175421f164',
    }
    url = f"https://api.openrouteservice.org/v2/directions/driving-car?start={start_coords[1]},{start_coords[0]}&end={end_coords[1]},{end_coords[0]}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json()['features']:
        coords = response.json()['features'][0]['geometry']['coordinates']
        return [(c[1], c[0]) for c in coords]
    return []

def get_departement(coords):
    latitude, longitude = coords
    # print("----------------------> MMMMMMMM COORDS ---------------------------->", coords)
    url_depart = f"https://geo.api.gouv.fr/communes?lat={latitude}&lon={longitude}&fields=codeDepartement&format=json&geometry=centre"
    response = requests.get(url_depart)
    data = response.json()
    # print("----------------------> MMMMMMMM DATA IN GET_DEPARTEMENT ---------------------------->", data)
    # Vérifiez si la réponse contient des données
    if data:
        departement_depart = data[0]["codeDepartement"]
        url_departement = f"https://geo.api.gouv.fr/departements?code={departement_depart}&fields=nom,code,codeRegion"
        response_departement = requests.get(url_departement)
        data_departement = response_departement.json()

        if data_departement:
            nom_departement = data_departement[0]["nom"]
            return nom_departement
    return None  # ou retourner une valeur par défaut ou gérer l'erreur différemment


def get_nearby_stations(departement):
    """Fonction pour obtenir les bornes de recharge à proximité"""
    stations=[]
    nbornes = 20
    url = f"https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/bornes-irve/records?select=xlongitude%2Cylatitude%2Cregion%2Cdepartement%2Ccode_insee_commune&limit={nbornes}&refine=departement%3A%22{departement}%22"
    
    response = requests.get(url).content
    try:
        stations = json.loads(response)["results"]
        return stations
    except json.JSONDecodeError:
        print("La réponse n'est pas un JSON valide : ", response)


# Afficher bornes entre les 2 villes 
def get_nearby_stations_along_route(route_coords, departement, max_distance_km=10):
    """Fonction pour obtenir les bornes de recharge à proximité du trajet entre deux villes"""
    stations = get_nearby_stations(departement)
    nearby_stations = []
    for station in stations:
        station_coords = (station['ylatitude'], station['xlongitude'])
        # Vérifiez si la station est à moins de 10 km d'un des points de la route
        if any(great_circle(station_coords, point).km <= max_distance_km for point in route_coords):
            nearby_stations.append(station)
    return nearby_stations


def get_list_vehicles():
    url_list = "https://api.chargetrip.io/graphql"
    
    headers = {
        "x-client-id": "655244460932825baf12f834",
        "x-app-id": "655244460932825baf12f836",
        "Content-Type": "application/json"
    }

    vehicles = []
    page = 0
    size = 100

    while True:
        query = {
            "query": """
                query vehicleList($page: Int, $size: Int) {
                    vehicleList(page: $page, size: $size) {
                        id
                        naming {
                            make
                            model
                            chargetrip_version
                        }
                        media {
                            image {
                                thumbnail_url
                            }
                        }
                        range {
                            chargetrip_range {
                                best
                                worst
                            }
                        }
                    }
                }
            """,
            "variables": {
                "page": page,
                "size": size
            }
        }

        response = requests.post(url_list, json=query, headers=headers)

        if response.status_code == 200:
            data = response.json()
            batch_vehicles = data.get("data", {}).get("vehicleList") or []  # Use an empty list if batch_vehicles is None
            vehicles.extend(batch_vehicles)
            
            # If fewer than 100 vehicles are returned, we've fetched all vehicles.
            if len(batch_vehicles) < 100:
                break

            # Otherwise, move to the next page.
            page += 1
        else:
            # In case of an error, break the loop.
            break

    return vehicles

@app.route('/')
def liste_vehicules():
    vehicules = get_list_vehicles()
    return render_template('page.html', vehicules=vehicules)


@app.route('/', methods=['GET', 'POST'])
def index():
    vehicules = get_list_vehicles()
    if request.method == 'POST':
        if 'distance' in request.form:
            distance = float(request.form['distance'])
            autonomie = float(request.form['autonomie'])
            temps_chargement = float(request.form['tempsChargement'])
            
            temps_trajet = client.service.calculer_temps_trajet(distance, autonomie, temps_chargement)
            heures, minutes = divmod(temps_trajet, 60)
            resultat = f"Le temps de trajet estimé est : {int(heures)} heures et {int(minutes)} minutes."
            
            return render_template('page.html', resultat=resultat,vehicules=vehicules)
    
    return render_template('page.html', resultat='')


@app.route('/afficher_carte', methods=['GET', 'POST'])
def afficher_carte():
    vehicules=get_list_vehicles()
    start_coords = None
    end_coords = None
    route_coords = []
    stations = []
    distance = None
    if request.method == 'POST':
        start_city = request.form['start_city']
        end_city = request.form['end_city']
        start_coords = get_coordinates(start_city)
        end_coords = get_coordinates(end_city)
        if start_coords and end_coords:
            route_coords = get_route(start_coords, end_coords)
            # print("----------------------> MMMMMMMM LES POINTS SUR ENTRE LES 2 VILLES ---------------------------->", route_coords)
            # Get department
            departement_depart = get_departement(start_coords)
            # print("----------------------> MMMMMMMM DÉPART ---------------------------->", departement_depart)
            departement_arrive = get_departement(end_coords)
            # print("----------------------> MMMMMMMM ARRIVÉE ---------------------------->", departement_arrive)
            stations_depart = get_nearby_stations_along_route(route_coords, departement_depart)
            # print("----------------------> MMMMMMMM STATIONS DE DEPART ---------------------------->", stations_depart)
            stations_arrive = get_nearby_stations_along_route(route_coords, departement_arrive)
            # print("----------------------> MMMMMMMM STATIONS DE ARRIVÉE ---------------------------->", stations_arrive)
            
            # Obtenez les stations le long de la route en passant la liste des coordonnées de la route
            stations = stations_depart + stations_arrive
            print(stations)
            # print("----------------------> STATIONS ALONG ROUTE ---------------------------->", stations)
            # Effectuez une requête à votre API REST pour récupérer la distance
            response = requests.get(f'http://127.0.0.1:5000/cartographie/{start_coords[0]},{start_coords[1]}/{end_coords[0]},{end_coords[1]}')
            if response.status_code == 200:
                data = response.json()
                distance = data.get('distance')
        else:
            print("Impossible de trouver les coordonnées pour les villes fournies.")
    
    return render_template('page.html', start_coords=start_coords, end_coords=end_coords, route_coords=route_coords, stations=stations,vehicules=vehicules)


if __name__ == '__main__':
    app.run(debug=True)