"""
Module pour l'intégration du modèle de machine learning
Version corrigée avec logique de calcul de temps cohérente
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
            
            # Prédire la durée avec le modèle ML (en minutes)
            predicted_duration_minutes = self.predictor.predict_duration(
                start_point_ml,
                end_point_ml,
                route['distance'],
                current_hour,
                current_day
            )
            
            # Convertir en secondes
            predicted_duration_seconds = predicted_duration_minutes * 60
            
            # Obtenir les facteurs d'ajustement
            traffic_factor = TrafficDataService.get_traffic_factor(None, current_hour)
            road_type_factor = TrafficDataService.get_road_type_factor(route['path'])
            
            # LOGIQUE CORRIGÉE : Calcul cohérent de la durée finale
            # 1. Partir de la prédiction ML de base
            base_duration = predicted_duration_seconds
            
            # 2. Appliquer le facteur de trafic (multiplicateur)
            # traffic_factor > 1 = trafic dense = plus lent
            # traffic_factor < 1 = trafic fluide = plus rapide
            duration_with_traffic = base_duration * traffic_factor
            
            # 3. Appliquer le facteur de type de route (multiplicateur inverse)
            # road_type_factor > 1 = route rapide = diviser pour aller plus vite
            # road_type_factor < 1 = route lente = diviser par un nombre < 1 = multiplier
            final_duration = duration_with_traffic / road_type_factor
            
            # 4. Validation et limites de sécurité
            final_duration = self._validate_duration(final_duration, route['distance'])
            
            # Mettre à jour la durée prédite
            route['duration'] = final_duration
            route['traffic_factor'] = traffic_factor
            route['road_type_factor'] = road_type_factor
            route['ml_prediction_minutes'] = predicted_duration_minutes
            
            # Formatage du temps en minutes et secondes
            minutes = int(route['duration'] // 60)
            seconds = int(route['duration'] % 60)
            route['duration_text'] = f"{minutes} min {seconds:02d} sec"
            
            # Ajouter des informations de debug
            route['debug_info'] = {
                'base_duration_sec': base_duration,
                'duration_with_traffic_sec': duration_with_traffic,
                'final_duration_sec': final_duration,
                'average_speed_kmh': round((route['distance'] / 1000) / (final_duration / 3600), 1)
            }
            
            return route
        except Exception as e:
            print(f"Erreur lors de la prédiction de l'itinéraire optimal: {e}")
            # En cas d'erreur, utiliser le service de routage standard
            return RoutingService.get_route(start_point, end_point)
    
    def _validate_duration(self, duration, distance):
        """
        Valide et ajuste la durée calculée pour s'assurer qu'elle est réaliste
        
        Args:
            duration: Durée en secondes
            distance: Distance en mètres
            
        Returns:
            Durée validée en secondes
        """
        # Vitesses limites réalistes pour un environnement urbain
        MIN_SPEED_KMH = 5   # 5 km/h minimum (embouteillages extrêmes)
        MAX_SPEED_KMH = 80  # 80 km/h maximum (routes rapides urbaines)
        
        # Calculer les durées limites
        min_duration = (distance / 1000) / MAX_SPEED_KMH * 3600  # secondes
        max_duration = (distance / 1000) / MIN_SPEED_KMH * 3600  # secondes
        
        # Appliquer les limites
        validated_duration = max(min_duration, min(duration, max_duration))
        
        # Log si des ajustements ont été faits
        if validated_duration != duration:
            original_speed = (distance / 1000) / (duration / 3600)
            new_speed = (distance / 1000) / (validated_duration / 3600)
            print(f"Durée ajustée: {original_speed:.1f} km/h -> {new_speed:.1f} km/h")
        
        return validated_duration
    
    def calculate_realistic_duration(self, distance, traffic_factor, road_type_factor):
        """
        Calcule une durée réaliste basée sur des vitesses moyennes urbaines
        
        Args:
            distance: Distance en mètres
            traffic_factor: Facteur de trafic
            road_type_factor: Facteur de type de route
            
        Returns:
            Durée en secondes
        """
        # Vitesse de base urbaine : 40 km/h
        base_speed_kmh = 40
        
        # Ajuster la vitesse selon les facteurs
        # traffic_factor > 1 = trafic dense = vitesse réduite
        adjusted_speed = base_speed_kmh / traffic_factor
        
        # road_type_factor > 1 = route rapide = vitesse augmentée
        final_speed = adjusted_speed * road_type_factor
        
        # Calculer la durée
        duration_hours = (distance / 1000) / final_speed
        duration_seconds = duration_hours * 3600
        
        return duration_seconds

