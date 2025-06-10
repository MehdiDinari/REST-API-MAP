"""
Module pour générer des données d'entraînement pour le modèle de machine learning
"""
import numpy as np
import pandas as pd
import random
import math
import os
from datetime import datetime, timedelta

class DataGenerator:
    """
    Classe pour générer des données d'entraînement pour le modèle de machine learning
    """
    def __init__(self, output_dir):
        """
        Initialise le générateur de données
        """
        self.output_dir = output_dir
        
        # Coordonnées approximatives de Fès, Maroc
        self.center_lat = 34.0333
        self.center_lon = -5.0000
        
        # Rayon de la zone (en degrés)
        self.radius = 0.05
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_random_point(self):
        """
        Génère un point aléatoire dans la zone de Fès
        """
        # Angle aléatoire
        angle = random.uniform(0, 2 * math.pi)
        
        # Distance aléatoire du centre (pour une distribution plus uniforme)
        distance = self.radius * math.sqrt(random.uniform(0, 1))
        
        # Calculer les coordonnées
        lat = self.center_lat + distance * math.cos(angle)
        lon = self.center_lon + distance * math.sin(angle)
        
        return lat, lon
    
    def generate_traffic_data(self, num_samples=1000):
        """
        Génère des données de trafic simulées
        """
        data = []
        
        # Générer des données pour différentes heures de la journée
        for _ in range(num_samples):
            # Générer deux points aléatoires
            start_lat, start_lon = self.generate_random_point()
            end_lat, end_lon = self.generate_random_point()
            
            # Calculer la distance à vol d'oiseau
            distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)
            
            # Heure aléatoire de la journée
            hour = random.randint(0, 23)
            
            # Facteur de trafic en fonction de l'heure
            # Heures de pointe : 8h-9h et 17h-19h
            if hour in [8, 17, 18]:
                traffic_factor = random.uniform(1.3, 1.7)  # Trafic dense
            elif hour in [7, 9, 16, 19]:
                traffic_factor = random.uniform(1.1, 1.4)  # Trafic modéré
            elif hour >= 23 or hour <= 5:
                traffic_factor = random.uniform(0.7, 0.9)  # Trafic fluide (nuit)
            else:
                traffic_factor = random.uniform(0.9, 1.1)  # Trafic normal
            
            # Vitesse moyenne en fonction du trafic (km/h)
            speed = 50 / traffic_factor
            
            # Durée du trajet (en minutes)
            duration = (distance / 1000) / speed * 60
            
            # Ajouter un peu de bruit aléatoire
            duration = duration * random.uniform(0.9, 1.1)
            
            # Jour de la semaine (0 = lundi, 6 = dimanche)
            day_of_week = random.randint(0, 6)
            
            # Facteur jour de semaine
            if day_of_week >= 5:  # Weekend
                day_factor = random.uniform(0.8, 1.0)
            else:  # Jour de semaine
                day_factor = random.uniform(1.0, 1.2)
            
            # Appliquer le facteur jour de semaine
            duration = duration * day_factor
            
            # Ajouter les données
            data.append({
                'start_lat': start_lat,
                'start_lon': start_lon,
                'end_lat': end_lat,
                'end_lon': end_lon,
                'distance': distance,
                'hour': hour,
                'day_of_week': day_of_week,
                'duration': duration
            })
        
        # Créer un DataFrame
        df = pd.DataFrame(data)
        
        # Sauvegarder les données
        csv_path = os.path.join(self.output_dir, 'traffic_data.csv')
        df.to_csv(csv_path, index=False)
        
        print(f"Données sauvegardées dans: {csv_path}")
        
        return df

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcule la distance à vol d'oiseau entre deux points en mètres
        """
        R = 6371000  # Rayon de la Terre en mètres
        
        # Conversion en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Différence de latitude et longitude
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Formule de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance

if __name__ == "__main__":
    # Générer des données d'entraînement
    # Utiliser un chemin absolu pour éviter les problèmes de chemin relatif
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    
    generator = DataGenerator(data_dir)
    df = generator.generate_traffic_data(1000)
    print(f"Données générées : {len(df)} échantillons")

