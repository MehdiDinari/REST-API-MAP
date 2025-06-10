"""
Module pour l'intégration du modèle de machine learning
Version simplifiée sans modèle ML pour éviter les erreurs I/O
"""
import os
from .utils import RoutingService, TrafficDataService
from datetime import datetime
import math

class MLIntegration:
    """
    Classe pour l'intégration du modèle de machine learning
    Version simplifiée utilisant des calculs heuristiques
    """
    def __init__(self):
        """
        Initialise l'intégration sans charger le modèle ML
        """
        self.model_loaded = False
        print("MLIntegration initialisé en mode heuristique (sans modèle ML)")
    
    def predict_optimal_route(self, start_point, end_point):
        """
        Prédit le meilleur itinéraire entre deux points
        Utilise des calculs heuristiques au lieu du modèle ML
        
        Args:
            start_point: [longitude, latitude] du point de départ
            end_point: [longitude, latitude] du point d'arrivée
        
        Returns:
            Dictionnaire avec les informations de l'itinéraire optimisé
        """
        # Obtenir l'heure et le jour actuels
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()
        
        try:
            # Calculer l'itinéraire de base avec l'API OSRM
            route = RoutingService.get_route(start_point, end_point)
            
            # Obtenir les facteurs d'ajustement
            traffic_factor = TrafficDataService.get_traffic_factor(None, current_hour)
            road_type_factor = TrafficDataService.get_road_type_factor(route['path'])
            
            # LOGIQUE CORRIGÉE : Calcul cohérent de la durée finale
            # 1. Calculer une durée de base réaliste
            base_duration = self._calculate_realistic_base_duration(route['distance'])
            
            # 2. Appliquer le facteur de trafic
            # traffic_factor > 1 = trafic dense = plus lent
            # traffic_factor < 1 = trafic fluide = plus rapide
            duration_with_traffic = base_duration * traffic_factor
            
            # 3. Appliquer le facteur de type de route
            # road_type_factor > 1 = route rapide = temps réduit
            # road_type_factor < 1 = route lente = temps augmenté
            final_duration = duration_with_traffic / road_type_factor
            
            # 4. Validation et limites de sécurité
            final_duration = self._validate_duration(final_duration, route['distance'])
            
            # Mettre à jour la durée prédite
            route['duration'] = final_duration
            route['traffic_factor'] = traffic_factor
            route['road_type_factor'] = road_type_factor
            
            # Formatage du temps en minutes et secondes
            minutes = int(route['duration'] // 60)
            seconds = int(route['duration'] % 60)
            route['duration_text'] = f"{minutes} min {seconds:02d} sec"
            
            # Ajouter des informations de debug
            route['debug_info'] = {
                'base_duration_sec': base_duration,
                'duration_with_traffic_sec': duration_with_traffic,
                'final_duration_sec': final_duration,
                'average_speed_kmh': round((route['distance'] / 1000) / (final_duration / 3600), 1),
                'calculation_method': 'heuristic'
            }
            
            return route
        except Exception as e:
            print(f"Erreur lors de la prédiction de l'itinéraire optimal: {e}")
            # En cas d'erreur, utiliser le service de routage standard
            return RoutingService.get_route(start_point, end_point)
    
    def _calculate_realistic_base_duration(self, distance):
        """
        Calcule une durée de base réaliste basée sur la distance
        
        Args:
            distance: Distance en mètres
            
        Returns:
            Durée de base en secondes
        """
        # Vitesses moyennes réalistes selon la distance
        if distance < 1000:  # Moins de 1 km - circulation urbaine dense
            base_speed_kmh = 25
        elif distance < 3000:  # 1-3 km - circulation urbaine
            base_speed_kmh = 35
        elif distance < 10000:  # 3-10 km - circulation urbaine/périurbaine
            base_speed_kmh = 45
        else:  # Plus de 10 km - routes principales
            base_speed_kmh = 55
        
        # Calculer la durée en secondes
        duration_hours = (distance / 1000) / base_speed_kmh
        duration_seconds = duration_hours * 3600
        
        return duration_seconds
    
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
        MIN_SPEED_KMH = 10   # 10 km/h minimum (embouteillages)
        MAX_SPEED_KMH = 70   # 70 km/h maximum (routes rapides urbaines)
        
        # Calculer les durées limites
        min_duration = (distance / 1000) / MAX_SPEED_KMH * 3600  # secondes
        max_duration = (distance / 1000) / MIN_SPEED_KMH * 3600  # secondes
        
        # Appliquer les limites
        validated_duration = max(min_duration, min(duration, max_duration))
        
        # Log si des ajustements ont été faits
        if abs(validated_duration - duration) > 10:  # Plus de 10 secondes de différence
            original_speed = (distance / 1000) / (duration / 3600)
            new_speed = (distance / 1000) / (validated_duration / 3600)
            print(f"Durée ajustée: {original_speed:.1f} km/h -> {new_speed:.1f} km/h")
        
        return validated_duration

