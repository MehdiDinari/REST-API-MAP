"""
Module pour prédire le meilleur chemin en utilisant le modèle de machine learning
"""
import joblib
import os
import numpy as np
from datetime import datetime
import math

class RoutePredictor:
    """
    Classe pour prédire le meilleur chemin en utilisant le modèle de machine learning
    """
    def __init__(self, model_dir):
        """
        Initialise le prédicteur de chemin
        """
        self.model_dir = model_dir
        self.model = None
        self.features = None
        
        # Charger le modèle
        self.load_model()
    
    def load_model(self):
        """
        Charge le modèle de machine learning
        """
        model_path = os.path.join(self.model_dir, 'route_predictor_model.joblib')
        features_path = os.path.join(self.model_dir, 'features.txt')
        
        # Vérifier si le modèle existe
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Le modèle n'existe pas: {model_path}")
        
        # Charger le modèle
        self.model = joblib.load(model_path)
        
        # Charger les caractéristiques
        with open(features_path, 'r') as f:
            self.features = f.read().splitlines()
    
    def predict_duration(self, start_point, end_point, distance, hour=None, day_of_week=None):
        """
        Prédit la durée d'un trajet entre deux points
        
        Args:
            start_point: [latitude, longitude] du point de départ
            end_point: [latitude, longitude] du point d'arrivée
            distance: distance en mètres
            hour: heure de la journée (0-23), si None, utilise l'heure actuelle
            day_of_week: jour de la semaine (0-6, 0=lundi), si None, utilise le jour actuel
        
        Returns:
            Durée prédite en minutes
        """
        # Vérifier si le modèle est chargé
        if self.model is None:
            self.load_model()
        
        # Utiliser l'heure et le jour actuels si non spécifiés
        if hour is None:
            hour = datetime.now().hour
        
        if day_of_week is None:
            # En Python, datetime.weekday() retourne 0 pour lundi, 6 pour dimanche
            day_of_week = datetime.now().weekday()
        
        # Créer les données d'entrée pour le modèle
        input_data = {
            'start_lat': start_point[0],
            'start_lon': start_point[1],
            'end_lat': end_point[0],
            'end_lon': end_point[1],
            'distance': distance,
            'hour': hour,
            'day_of_week': day_of_week
        }
        
        # Convertir en tableau numpy
        X = np.array([[input_data[feature] for feature in self.features]])
        
        # Prédire la durée
        duration = self.model.predict(X)[0]
        
        # Appliquer des ajustements supplémentaires basés sur des heuristiques
        duration = self._apply_heuristic_adjustments(duration, distance, hour, day_of_week)
        
        return duration
    
    def _apply_heuristic_adjustments(self, duration, distance, hour, day_of_week):
        """
        Applique des ajustements heuristiques à la durée prédite
        
        Args:
            duration: Durée prédite en minutes
            distance: Distance en mètres
            hour: Heure de la journée (0-23)
            day_of_week: Jour de la semaine (0-6, 0=lundi)
            
        Returns:
            Durée ajustée en minutes
        """
        # Ajustement pour les très courtes distances
        if distance < 1000:
            # Pour les très courtes distances, le modèle peut sous-estimer le temps
            # car il ne prend pas en compte le temps de démarrage, les feux, etc.
            min_duration = 2.0  # Au moins 2 minutes pour les trajets très courts
            duration = max(duration, min_duration)
        
        # Ajustement pour les heures de pointe
        if hour in [8, 9, 17, 18, 19]:
            # Augmenter légèrement la durée aux heures de pointe
            # même si le modèle prend déjà en compte l'heure
            duration *= 1.05
        
        # Ajustement pour les weekends
        if day_of_week >= 5:  # Samedi et dimanche
            # Réduire légèrement la durée le weekend
            duration *= 0.95
        
        # Ajustement pour la nuit
        if hour >= 22 or hour <= 5:
            # Réduire légèrement la durée la nuit
            duration *= 0.9
        
        return duration
    
    def optimize_route(self, routes, hour=None, day_of_week=None):
        """
        Optimise un itinéraire en fonction des prédictions du modèle
        
        Args:
            routes: liste de routes possibles, chaque route est un dictionnaire avec:
                - start_point: [latitude, longitude] du point de départ
                - end_point: [latitude, longitude] du point d'arrivée
                - distance: distance en mètres
                - path: liste de points intermédiaires
            hour: heure de la journée (0-23), si None, utilise l'heure actuelle
            day_of_week: jour de la semaine (0-6, 0=lundi), si None, utilise le jour actuel
        
        Returns:
            La meilleure route avec la durée prédite
        """
        best_route = None
        best_duration = float('inf')
        
        for route in routes:
            # Prédire la durée
            duration = self.predict_duration(
                route['start_point'],
                route['end_point'],
                route['distance'],
                hour,
                day_of_week
            )
            
            # Mettre à jour la meilleure route
            if duration < best_duration:
                best_duration = duration
                best_route = route.copy()
                best_route['duration'] = duration * 60  # Convertir en secondes
                
                # Formatage du temps en minutes et secondes
                minutes = int(best_route['duration'] // 60)
                seconds = int(best_route['duration'] % 60)
                best_route['duration_text'] = f"{minutes} min {seconds} sec"
        
        return best_route
    
    def calculate_route_complexity(self, path):
        """
        Calcule la complexité d'un itinéraire basée sur le nombre de virages
        
        Args:
            path: Liste de points [lon, lat] de l'itinéraire
            
        Returns:
            Score de complexité (plus élevé = plus complexe)
        """
        if len(path) < 3:
            return 0
        
        complexity = 0
        
        # Calculer les angles entre les segments consécutifs
        for i in range(1, len(path) - 1):
            # Calculer les vecteurs entre les points
            v1 = [path[i][0] - path[i-1][0], path[i][1] - path[i-1][1]]
            v2 = [path[i+1][0] - path[i][0], path[i+1][1] - path[i][1]]
            
            # Normaliser les vecteurs
            v1_norm = math.sqrt(v1[0]**2 + v1[1]**2)
            v2_norm = math.sqrt(v2[0]**2 + v2[1]**2)
            
            if v1_norm == 0 or v2_norm == 0:
                continue
            
            v1 = [v1[0]/v1_norm, v1[1]/v1_norm]
            v2 = [v2[0]/v2_norm, v2[1]/v2_norm]
            
            # Calculer le produit scalaire
            dot_product = v1[0]*v2[0] + v1[1]*v2[1]
            
            # Limiter le produit scalaire à [-1, 1] pour éviter les erreurs numériques
            dot_product = max(-1, min(1, dot_product))
            
            # Calculer l'angle en radians
            angle = math.acos(dot_product)
            
            # Convertir en degrés
            angle_deg = math.degrees(angle)
            
            # Ajouter à la complexité si l'angle est significatif (> 20 degrés)
            if angle_deg > 20:
                complexity += angle_deg / 90.0  # Normaliser par rapport à un virage à 90 degrés
        
        return complexity

