from django.db import models
from pymongo import MongoClient
from django.conf import settings
import json
from datetime import datetime

# Connexion à MongoDB
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]

# Collections MongoDB
locations_collection = db['locations']
routes_collection = db['routes']
traffic_data_collection = db['traffic_data']

class PreExtractedLocation(models.Model):
    """
    Modèle pour stocker les lieux pré-extraits de Fès depuis OpenStreetMap
    """
    name = models.CharField(max_length=500, db_index=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    location_type = models.CharField(max_length=100, null=True, blank=True)
    
    # Index pour améliorer les performances de recherche
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['location_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.location_type})"
    
    @property
    def coordinates(self):
        """Retourne les coordonnées au format [longitude, latitude]"""
        return [self.longitude, self.latitude]

class MongoDBManager:
    """
    Gestionnaire pour les opérations MongoDB
    """
    @staticmethod
    def save_location(name, coordinates):
        """
        Enregistre un lieu dans MongoDB
        """
        location_data = {
            'name': name,
            'coordinates': coordinates,  # [longitude, latitude]
            'type': 'Point',
        }
        return locations_collection.insert_one(location_data).inserted_id
    
    @staticmethod
    def find_location_by_name(name):
        """
        Recherche un lieu par son nom
        """
        return locations_collection.find_one({'name': {'$regex': name, '$options': 'i'}})
    
    @staticmethod
    def find_locations_near(coordinates, max_distance=1000):
        """
        Recherche des lieux à proximité des coordonnées données
        """
        return list(locations_collection.find({
            'coordinates': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': coordinates
                    },
                    '$maxDistance': max_distance
                }
            }
        }))
    
    @staticmethod
    def save_route(start_point, end_point, path, distance, duration, duration_text=''):
        """
        Enregistre un itinéraire dans MongoDB
        
        Args:
            start_point: Point de départ [longitude, latitude]
            end_point: Point d'arrivée [longitude, latitude]
            path: Liste de coordonnées [[lon1, lat1], [lon2, lat2], ...]
            distance: Distance en mètres
            duration: Durée en secondes
            duration_text: Durée formatée en texte (ex: "5 min 30 sec")
        """
        # Convertir les points en chaînes pour éviter l'erreur "cannot index parallel arrays"
        start_point_str = f"{start_point[0]},{start_point[1]}"
        end_point_str = f"{end_point[0]},{end_point[1]}"
        
        # Créer un identifiant unique pour l'itinéraire
        route_id = f"{start_point_str}_to_{end_point_str}"
        
        route_data = {
            'route_id': route_id,
            'start_point_str': start_point_str,
            'end_point_str': end_point_str,
            'start_point_lon': start_point[0],
            'start_point_lat': start_point[1],
            'end_point_lon': end_point[0],
            'end_point_lat': end_point[1],
            'path': path,
            'distance': distance,
            'duration': duration,
            'duration_text': duration_text,
            'created_at': datetime.now()
        }
        
        # Utiliser upsert pour éviter les doublons
        return routes_collection.update_one(
            {'route_id': route_id},
            {'$set': route_data},
            upsert=True
        ).upserted_id
    
    @staticmethod
    def find_route(start_point, end_point):
        """
        Recherche un itinéraire existant entre deux points
        """
        # Convertir les points en chaînes pour la recherche
        start_point_str = f"{start_point[0]},{start_point[1]}"
        end_point_str = f"{end_point[0]},{end_point[1]}"
        
        # Créer un identifiant unique pour l'itinéraire
        route_id = f"{start_point_str}_to_{end_point_str}"
        
        route = routes_collection.find_one({
            'route_id': route_id
        })
        
        if route:
            # Reconstruire les points à partir des coordonnées stockées
            route['start_point'] = [route['start_point_lon'], route['start_point_lat']]
            route['end_point'] = [route['end_point_lon'], route['end_point_lat']]
        
        return route
    
    @staticmethod
    def save_traffic_data(segment, timestamp, speed, congestion_level):
        """
        Enregistre des données de trafic pour un segment de route
        """
        traffic_data = {
            'segment': segment,  # Identifiant du segment de route
            'timestamp': timestamp,
            'speed': speed,  # Vitesse moyenne en km/h
            'congestion_level': congestion_level,  # Niveau de congestion (0-5),
        }
        return traffic_data_collection.insert_one(traffic_data).inserted_id
    
    @staticmethod
    def get_traffic_data(segment, start_time=None, end_time=None):
        """
        Récupère les données de trafic pour un segment de route
        """
        query = {'segment': segment}
        if start_time and end_time:
            query['timestamp'] = {'$gte': start_time, '$lte': end_time}
        
        return list(traffic_data_collection.find(query).sort('timestamp', -1))

# Créer les index nécessaires pour MongoDB
def create_mongodb_indexes():
    """
    Crée les index nécessaires pour MongoDB
    """
    # Index géospatial pour les recherches de proximité
    locations_collection.create_index([("coordinates", "2dsphere")])
    
    # Index pour les recherches de lieux par nom
    locations_collection.create_index([("name", "text")])
    
    # Index pour les recherches d'itinéraires
    routes_collection.create_index([("route_id", 1)], unique=True)
    
    # Index pour les données de trafic
    traffic_data_collection.create_index([("segment", 1), ("timestamp", -1)])

# Appel à la création des index
create_mongodb_indexes()

