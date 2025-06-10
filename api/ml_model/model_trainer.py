"""
Module pour entraîner le modèle de machine learning
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

class ModelTrainer:
    """
    Classe pour entraîner le modèle de machine learning
    """
    def __init__(self, data_dir, output_dir):
        """
        Initialise l'entraîneur de modèle
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self):
        """
        Charge les données d'entraînement
        """
        data_path = os.path.join(self.data_dir, 'traffic_data.csv')
        print(f"Chargement des données depuis: {data_path}")
        return pd.read_csv(data_path)
    
    def preprocess_data(self, df):
        """
        Prétraite les données pour l'entraînement
        """
        # Caractéristiques à utiliser pour la prédiction
        features = [
            'start_lat', 'start_lon', 'end_lat', 'end_lon',
            'distance', 'hour', 'day_of_week'
        ]
        
        # Variable cible
        target = 'duration'
        
        # Séparer les caractéristiques et la cible
        X = df[features]
        y = df[target]
        
        # Diviser les données en ensembles d'entraînement et de test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        return X_train, X_test, y_train, y_test, features
    
    def train_model(self):
        """
        Entraîne le modèle de machine learning
        """
        # Charger les données
        df = self.load_data()
        
        # Prétraiter les données
        X_train, X_test, y_train, y_test, features = self.preprocess_data(df)
        
        # Créer le pipeline avec mise à l'échelle et modèle
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ))
        ])
        
        # Entraîner le modèle
        pipeline.fit(X_train, y_train)
        
        # Évaluer le modèle
        y_pred = pipeline.predict(X_test)
        
        # Calculer les métriques
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        print(f"Évaluation du modèle:")
        print(f"MAE: {mae:.2f} minutes")
        print(f"RMSE: {rmse:.2f} minutes")
        print(f"R²: {r2:.4f}")
        
        # Sauvegarder le modèle
        model_path = os.path.join(self.output_dir, 'route_predictor_model.joblib')
        joblib.dump(pipeline, model_path)
        
        # Sauvegarder la liste des caractéristiques
        features_path = os.path.join(self.output_dir, 'features.txt')
        with open(features_path, 'w') as f:
            f.write('\n'.join(features))
        
        print(f"Modèle sauvegardé: {model_path}")
        
        return pipeline, features

if __name__ == "__main__":
    # Entraîner le modèle
    # Utiliser des chemins absolus pour éviter les problèmes de chemin relatif
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    
    trainer = ModelTrainer(data_dir, current_dir)
    model, features = trainer.train_model()

