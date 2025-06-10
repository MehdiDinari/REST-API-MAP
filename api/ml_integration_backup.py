"""
Module pour l'intégration du modèle de machine learning
"""
import os
from .ml_model.predictor import RoutePredictor
from .utils import RoutingService, TrafficDataService
from datetime import datetime

class MLIntegration:
    """
    Classe pour l'intégration du modèle de machine learning
    """
    def __init__(self):
        """
        Initialise l'intégration du modèle de machine learning
        """
        # Chemin vers le répertoire du modèle
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(current_dir, 'ml_model')
        
        # Initialiser le prédicteur
        try:
            self.predictor = RoutePredictor(model_dir)
            self.model_loaded = True
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            self.model_loaded = False
    
    def predict_optimal_route(self, start_point, end_point):
        """
        Prédit le meilleur itinéraire entre deux points
        
        Args:
            start_point: [longitude, latitude] du point de départ
            end_point: [longitude, latitude] du point d'arrivée
        
        Returns:
            Dictionnaire avec les informations de l'itinéraire optimisé
        """
        # Vérifier si le modèle est chargé
        if not self.model_loaded:
            # Si le modèle n'est pas chargé, utiliser le service de routage standard
            return RoutingService.get_route(start_point, end_point)
        
        # Obtenir l'heure et le jour actuels
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        
        try:
            # Calculer l'itinéraire de base avec l'API OSRM
            route = RoutingService.get_route(start_point, end_point)
            
            # Convertir les coordonnées pour le modèle (le modèle attend [lat, lon])
            start_point_ml = [start_point[1], start_point[0]]
            end_point_ml = [end_point[1], end_point[0]]
            
            # Prédire la durée avec le modèle
            predicted_duration = self.predictor.predict_duration(
                start_point_ml,
                end_point_ml,
                route['distance'],
                current_hour,
                current_day
            )
            
            # Obtenir le facteur de trafic actuel
            traffic_factor = TrafficDataService.get_traffic_factor(None, current_hour)
            
            # Obtenir le facteur de type de route
            road_type_factor = TrafficDataService.get_road_type_factor(route['path'])
            
            # Calculer la durée finale en tenant compte du trafic et du type de route
            # Le modèle ML donne une estimation de base, que nous ajustons avec les facteurs
            final_duration = predicted_duration * 60 * traffic_factor / road_type_factor
            
            # Mettre à jour la durée prédite
            route['duration'] = final_duration
            route['traffic_factor'] = traffic_factor
            route['road_type_factor'] = road_type_factor
            
            # Formatage du temps en minutes et secondes
            minutes = int(route['duration'] // 60)
            seconds = int(route['duration'] % 60)
            route['duration_text'] = f"{minutes} min {seconds} sec"
            
            return route
        except Exception as e:
            print(f"Erreur lors de la prédiction de l'itinéraire optimal: {e}")
            # En cas d'erreur, utiliser le service de routage standard
            return RoutingService.get_route(start_point, end_point)

