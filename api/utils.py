import requests
import math
from datetime import datetime
import json
import os
import time

class GeocodingService:
    """
    Service de géocodage utilisant Nominatim (OpenStreetMap)
    """
    @staticmethod
    def search_location(query, limit=5, city="Fès", country="Maroc"):
        """
        Recherche un lieu par son nom
        """
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{query}, {city}, {country}",
            "format": "json",
            "limit": limit,
            "addressdetails": 1
        }
        
        headers = {
            "User-Agent": "RouteFinder/1.0"
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                locations = []
                
                for result in results:
                    # Validation des coordonnées
                    try:
                        lon = float(result.get("lon"))
                        lat = float(result.get("lat"))
                        
                        location = {
                            "name": result.get("display_name"),
                            "coordinates": [lon, lat],
                            "type": "Point"
                        }
                        locations.append(location)
                    except (ValueError, TypeError):
                        print(f"Coordonnées invalides pour: {result.get('display_name')}")
                        continue
                
                return locations
            else:
                print(f"Erreur HTTP {response.status_code}: {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de requête géocodage: {str(e)}")
            return []

class RoutingService:
    """
    Service de calcul d'itinéraire utilisant Valhalla (Open Source Routing Engine)
    """
    @staticmethod
    def get_route(start_point, end_point, max_retries=3, retry_delay=1):
        """
        Calcule un itinéraire entre deux points en utilisant l'API Valhalla
        start_point et end_point sont des listes [longitude, latitude]
        """
        # Validation des coordonnées d'entrée
        if not RoutingService._validate_coordinates(start_point) or not RoutingService._validate_coordinates(end_point):
            print("Coordonnées invalides")
            return RoutingService.fallback_route(start_point, end_point)
        
        # Utilisation de l'API Valhalla pour obtenir un vrai trajet routier
        valhalla_url = "https://valhalla1.openstreetmap.de/route"
        
        # Préparation du payload JSON pour Valhalla
        payload = {
            "locations": [
                {"lat": start_point[1], "lon": start_point[0]},
                {"lat": end_point[1], "lon": end_point[0]}
            ],
            "costing": "auto",
            "shape_match": "edge_walk",
            "filters": {
                "attributes": ["edge.length", "edge.time"],
                "action": "include"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RouteFinder/1.0"
        }
        
        print(f"Valhalla Request URL: {valhalla_url}")
        print(f"Valhalla Request Payload: {json.dumps(payload, indent=2)}")
        
        # Appel à l'API Valhalla avec mécanisme de retry
        for attempt in range(max_retries):
            try:
                response = requests.post(valhalla_url, json=payload, headers=headers, timeout=120)
                
                print(f"Valhalla Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"Valhalla Response Keys: {list(data.keys())}")
                    
                    if "trip" in data and "legs" in data["trip"] and len(data["trip"]["legs"]) > 0:
                        trip = data["trip"]
                        leg = trip["legs"][0]  # Premier segment
                        
                        # Validation de la structure de la réponse
                        if "shape" not in leg:
                            print("Structure de réponse Valhalla invalide - pas de géométrie")
                            break
                        
                        # Extraction du chemin (coordonnées décodées du shape)
                        path = RoutingService._decode_polyline(leg["shape"])
                        
                        # Extraction de la distance en mètres
                        distance = leg.get("summary", {}).get("length", 0) * 1000  # Conversion km -> m
                        
                        # Extraction de la durée en secondes
                        duration = leg.get("summary", {}).get("time", 0)
                        
                        # Obtenir l'heure actuelle pour le facteur de trafic
                        current_hour = datetime.now().hour
                        
                        # Appliquer le facteur de trafic à la durée
                        traffic_factor = TrafficDataService.get_traffic_factor(None, current_hour)
                        adjusted_duration = duration * traffic_factor
                        
                        # Formatage du temps en minutes et secondes
                        minutes = int(adjusted_duration // 60)
                        seconds = int(adjusted_duration % 60)
                        
                        print(f"Valhalla Path Points: {len(path)}")
                        print(f"Valhalla First Point: {path[0] if path else 'N/A'}")
                        print(f"Valhalla Last Point: {path[-1] if path else 'N/A'}")
                        print(f"Valhalla Distance: {distance}m")
                        print(f"Valhalla Duration: {duration}s")
                        print(f"Traffic Factor: {traffic_factor}")
                        print(f"Adjusted Duration: {adjusted_duration}s")
                        
                        # Création de la réponse
                        return {
                            "path": path,
                            "distance": distance,
                            "duration": adjusted_duration,
                            "duration_text": f"{minutes} min {seconds:02d} sec",
                            "start_point": start_point,
                            "end_point": end_point,
                            "traffic_factor": traffic_factor,
                            "success": True
                        }
                    else:
                        error_msg = data.get('error', 'Aucune route trouvée')
                        print(f"Valhalla Error: {error_msg}")
                        
                elif response.status_code == 400:
                    print("Requête Valhalla invalide - arrêt des tentatives")
                    print(f"Response: {response.text}")
                    break
                else:
                    print(f"Erreur HTTP Valhalla: {response.status_code}")
                    print(f"Response: {response.text}")
                        
                # Si nous sommes ici, c'est que la requête a échoué
                if attempt < max_retries - 1:
                    print(f"Tentative {attempt + 1}/{max_retries} après {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponentiel
                    
            except requests.exceptions.RequestException as e:
                print(f"Erreur de requête Valhalla: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Tentative {attempt + 1}/{max_retries} après {retry_delay}s")
                    time.sleep(retry_delay)
                    retry_delay *= 2
            except (KeyError, ValueError, TypeError) as e:
                print(f"Erreur de traitement des données Valhalla: {str(e)}")
                break
        
        # En cas d'échec après tous les essais, utiliser la méthode de secours
        print("Utilisation du calcul d'itinéraire de secours")
        return RoutingService.fallback_route(start_point, end_point)
    
    @staticmethod
    def _decode_polyline(encoded_string, precision=6):
        """
        Décode une polyline encodée (format utilisé par Valhalla)
        """
        try:
            coordinates = []
            index = 0
            lat = 0
            lng = 0
            factor = 10 ** precision

            while index < len(encoded_string):
                # Décodage latitude
                shift = 0
                result = 0
                while True:
                    byte = ord(encoded_string[index]) - 63
                    index += 1
                    result |= (byte & 0x1f) << shift
                    shift += 5
                    if byte < 0x20:
                        break
                
                lat_change = ~(result >> 1) if (result & 1) else (result >> 1)
                lat += lat_change

                # Décodage longitude
                shift = 0
                result = 0
                while True:
                    byte = ord(encoded_string[index]) - 63
                    index += 1
                    result |= (byte & 0x1f) << shift
                    shift += 5
                    if byte < 0x20:
                        break
                
                lng_change = ~(result >> 1) if (result & 1) else (result >> 1)
                lng += lng_change

                coordinates.append([lng / factor, lat / factor])

            return coordinates
            
        except Exception as e:
            print(f"Erreur de décodage polyline: {str(e)}")
            return []
    
    @staticmethod
    def _validate_coordinates(point):
        """
        Valide que les coordonnées sont correctes
        """
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            return False
        
        try:
            lon, lat = float(point[0]), float(point[1])
            # Validation des limites géographiques
            if -180 <= lon <= 180 and -90 <= lat <= 90:
                return True
        except (ValueError, TypeError):
            pass
        
        return False
    
    @staticmethod
    def fallback_route(start_point, end_point):
        """
        Méthode de secours pour calculer un itinéraire si l'API Valhalla échoue
        """
        try:
            # Simulation d'un itinéraire avec quelques points intermédiaires
            path = RoutingService.generate_path(start_point, end_point, 35)
            
            # Calcul de la distance réelle en additionnant les segments du chemin
            distance = 0
            for i in range(len(path) - 1):
                segment_distance = RoutingService.haversine_distance(
                    path[i][1], path[i][0],
                    path[i+1][1], path[i+1][0]
                )
                distance += segment_distance
            
            # Ajout d'un facteur de correction pour simuler les routes réelles
            # Les routes réelles sont généralement 20-30% plus longues que la ligne droite
            road_winding_factor = 1.3
            distance = distance * road_winding_factor
            
            # Obtenir l'heure actuelle pour le facteur de trafic
            current_hour = datetime.now().hour
            
            # Estimation de la vitesse moyenne en fonction du trafic
            # Vitesse de base: 50 km/h en ville
            traffic_factor = TrafficDataService.get_traffic_factor(None, current_hour)
            road_type_factor = TrafficDataService.get_road_type_factor(path)
            base_speed_kmh = 50
            speed_kmh = base_speed_kmh * road_type_factor / traffic_factor
            
            # Protection contre les vitesses trop faibles
            speed_kmh = max(speed_kmh, 10)  # Minimum 10 km/h
            
            # Calcul de la durée en secondes
            # distance en mètres, vitesse en km/h
            duration = (distance / 1000) / speed_kmh * 3600
            
            # Formatage du temps en minutes et secondes
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            
            return {
                "path": path,
                "distance": distance,
                "duration": duration,
                "duration_text": f"{minutes} min {seconds:02d} sec",
                "start_point": start_point,
                "end_point": end_point,
                "traffic_factor": traffic_factor,
                "road_type_factor": road_type_factor,
                "success": False,  # Indique que c'est un calcul de secours
                "fallback": True
            }
            
        except Exception as e:
            print(f"Erreur dans le calcul de secours: {str(e)}")
            # Calcul ultra-basique en dernier recours
            direct_distance = RoutingService.haversine_distance(
                start_point[1], start_point[0],
                end_point[1], end_point[0]
            )
            
            return {
                "path": [start_point, end_point],
                "distance": direct_distance * 1.5,  # Facteur de route
                "duration": (direct_distance * 1.5 / 1000) / 30 * 3600,  # 30 km/h moyen
                "duration_text": "Estimation approximative",
                "start_point": start_point,
                "end_point": end_point,
                "traffic_factor": 1.0,
                "road_type_factor": 1.0,
                "success": False,
                "fallback": True,
                "error": "Calcul d'urgence utilisé"
            }
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calcule la distance à vol d'oiseau entre deux points en mètres
        """
        try:
            R = 6371000  # Rayon de la Terre en mètres
            
            # Conversion en radians
            lat1_rad = math.radians(float(lat1))
            lon1_rad = math.radians(float(lon1))
            lat2_rad = math.radians(float(lat2))
            lon2_rad = math.radians(float(lon2))
            
            # Différence de latitude et longitude
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Formule de Haversine
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return max(distance, 0)  # S'assurer que la distance n'est pas négative
            
        except (ValueError, TypeError) as e:
            print(f"Erreur dans le calcul de distance: {str(e)}")
            return 0
    
    @staticmethod
    def generate_path(start_point, end_point, num_points):
        """
        Génère un chemin avec des points intermédiaires entre start_point et end_point
        """
        try:
            path = [start_point]
            
            # Validation du nombre de points
            num_points = max(2, min(num_points, 100))  # Entre 2 et 100 points
            
            # Génération de points intermédiaires avec une simulation de route plus réaliste
            for i in range(1, num_points):
                ratio = i / num_points
                
                # Points de contrôle pour la courbe de Bézier
                control_point1 = [
                    start_point[0] + (end_point[0] - start_point[0]) * 0.3 + (math.sin(ratio * math.pi) * 0.002),
                    start_point[1] + (end_point[1] - start_point[1]) * 0.1 + (math.cos(ratio * math.pi) * 0.002)
                ]
                
                control_point2 = [
                    start_point[0] + (end_point[0] - start_point[0]) * 0.7 - (math.sin(ratio * math.pi) * 0.002),
                    start_point[1] + (end_point[1] - start_point[1]) * 0.9 - (math.cos(ratio * math.pi) * 0.002)
                ]
                
                # Calcul du point sur la courbe de Bézier
                t = ratio
                mt = 1 - t
                
                # Formule de la courbe de Bézier cubique
                lon = (mt*mt*mt*start_point[0] + 
                       3*mt*mt*t*control_point1[0] + 
                       3*mt*t*t*control_point2[0] + 
                       t*t*t*end_point[0])
                
                lat = (mt*mt*mt*start_point[1] + 
                       3*mt*mt*t*control_point1[1] + 
                       3*mt*t*t*control_point2[1] + 
                       t*t*t*end_point[1])
                
                # Ajout d'une petite variation pour simuler les irrégularités de la route
                lon_variation = math.sin(i * 0.7) * 0.0002
                lat_variation = math.cos(i * 0.7) * 0.0002
                
                path.append([lon + lon_variation, lat + lat_variation])
            
            path.append(end_point)
            return path
            
        except Exception as e:
            print(f"Erreur dans la génération du chemin: {str(e)}")
            # Retourner un chemin simple en cas d'erreur
            return [start_point, end_point]

class TrafficDataService:
    """
    Service de gestion des données de trafic
    """
    @staticmethod
    def get_traffic_factor(segment, hour_of_day):
        """
        Retourne un facteur de trafic pour un segment de route à une heure donnée
        
        Args:
            segment: Identifiant du segment de route (peut être None pour un facteur global)
            hour_of_day: Heure de la journée (0-23)
            
        Returns:
            Facteur de trafic (>1 pour trafic dense, <1 pour trafic fluide)
        """
        try:
            # Validation de l'heure
            if not isinstance(hour_of_day, int) or hour_of_day < 0 or hour_of_day > 23:
                hour_of_day = datetime.now().hour
            
            # Jours de la semaine (0=lundi, 6=dimanche)
            current_day = datetime.now().weekday()
            
            # Facteur de base selon le jour (weekend vs semaine)
            day_factor = 0.8 if current_day >= 5 else 1.0  # Weekend vs semaine
            
            # Heures de pointe : 8h-9h et 17h-19h
            if hour_of_day in [8, 17, 18]:
                return 1.5 * day_factor  # Trafic dense
            elif hour_of_day in [7, 9, 16, 19]:
                return 1.3 * day_factor  # Trafic modéré
            elif hour_of_day >= 23 or hour_of_day <= 5:
                return 0.8 * day_factor  # Trafic fluide (nuit)
            else:
                return 1.0 * day_factor  # Trafic normal
                
        except Exception as e:
            print(f"Erreur dans le calcul du facteur de trafic: {str(e)}")
            return 1.0  # Facteur neutre en cas d'erreur
    
    @staticmethod
    def get_road_type_factor(path):
        """
        Estime un facteur de vitesse basé sur le type de route
        
        Args:
            path: Liste de points du chemin
            
        Returns:
            Facteur de vitesse (>1 pour routes rapides, <1 pour routes lentes)
        """
        try:
            # Validation du chemin
            if not path or len(path) < 2:
                return 1.0
            
            # Calcul de la distance à vol d'oiseau entre le début et la fin
            start_point = path[0]
            end_point = path[-1]
            
            direct_distance = RoutingService.haversine_distance(
                start_point[1], start_point[0],
                end_point[1], end_point[0]
            )
            
            # Calcul de la distance totale du chemin
            total_distance = 0
            for i in range(len(path) - 1):
                segment_distance = RoutingService.haversine_distance(
                    path[i][1], path[i][0],
                    path[i+1][1], path[i+1][0]
                )
                total_distance += segment_distance
            
            # Ratio entre la distance totale et la distance directe
            if direct_distance > 0:
                sinuosity = total_distance / direct_distance
            else:
                return 1.0
            
            # Détermination du type de route en fonction de la sinuosité et de la distance
            if direct_distance > 10000:  # Plus de 10 km
                if sinuosity < 1.2:
                    return 1.3  # Autoroute
                else:
                    return 1.1  # Route nationale
            elif direct_distance > 3000:  # Entre 3 et 10 km
                if sinuosity < 1.3:
                    return 1.1  # Route nationale
                else:
                    return 0.9  # Route départementale
            else:  # Moins de 3 km
                if sinuosity < 1.2:
                    return 0.9  # Route urbaine principale
                else:
                    return 0.7  # Route urbaine secondaire ou ruelle
                    
        except Exception as e:
            print(f"Erreur dans le calcul du facteur de type de route: {str(e)}")
            return 1.0  # Facteur neutre en cas d'erreur

# Fonction utilitaire pour tester les services
def test_services():
    """
    Fonction de test pour les services
    """
    print("=== Test des services de géocodage et routage ===")
    
    # Test du géocodage
    print("\n1. Test du géocodage:")
    geocoding = GeocodingService()
    locations = geocoding.search_location("Université Sidi Mohamed Ben Abdellah")
    
    if locations:
        print(f"Trouvé {len(locations)} résultat(s):")
        for i, loc in enumerate(locations[:3]):  # Afficher les 3 premiers
            print(f"  {i+1}. {loc['name']}")
            print(f"     Coordonnées: {loc['coordinates']}")
    else:
        print("Aucun résultat trouvé")
    
    # Test du routage avec des coordonnées de Fès
    print("\n2. Test du routage:")
    start = [-5.0000, 34.0333]  # Fès centre approximatif
    end = [-5.0200, 34.0500]    # Autre point à Fès
    
    routing = RoutingService()
    route = routing.get_route(start, end)
    
    if route:
        print(f"Itinéraire calculé:")
        print(f"  Distance: {route['distance']:.0f}m")
        print(f"  Durée: {route['duration_text']}")
        print(f"  Points dans le chemin: {len(route['path'])}")
        print(f"  Succès API: {route.get('success', 'Non défini')}")
        print(f"  Service utilisé: {'Valhalla' if route.get('success') else 'Calcul de secours'}")
    else:
        print("Erreur dans le calcul d'itinéraire")

if __name__ == "__main__":
    test_services()